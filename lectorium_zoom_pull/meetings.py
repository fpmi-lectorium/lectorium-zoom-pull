import json
import os
import os.path
import subprocess
import urllib.parse
import typing as tp

import requests

from lectorium_zoom_pull.models import (
    AccountsRecordingsRequest,
    AccountsRecordingsResponse,
    Meeting,
    RecordingFile,
    FileType,
)


#
# List
#

def list_recordings(
    tokens,
    request: AccountsRecordingsRequest,
) -> AccountsRecordingsResponse:
    BASEURL = 'https://api.zoom.us/v2'

    rsp = requests.get(
        BASEURL + '/accounts/me/recordings',
        headers={
            'Authorization': 'Bearer {}'.format(tokens['access_token']),
            'Content-Type': 'application/json',
        },
        params=request.dict(by_alias=True, exclude_defaults=True),
    )

    if rsp.status_code != 200:
        with open('error.out', 'w') as fd:
            fd.write(rsp.text)

        raise ValueError('Bad response {}: {}'.format(
            rsp.status_code, rsp.text
        ))
    with open('raw-response.json', 'w') as fd:
        fd.write(rsp.text)
    return AccountsRecordingsResponse(**json.loads(rsp.text))



def fetch_all_meetings(
    tokens, account_id: str,
    from_date: str, to_date: str
) -> tp.List[Meeting]:
    meetings = []
    next_page_token = None
    while True:
        request = {
            'from': from_date,
            'to': to_date,
        }
        if next_page_token:
            request['next_page_token'] = next_page_token
        request = AccountsRecordingsRequest(**request)

        batch = list_recordings(tokens, request)
        print('Page size:', batch.page_size)
        print('Total records:', batch.total_records)
        meetings.extend(batch.meetings)

        next_page_token = batch.next_page_token
        if not next_page_token:
            break

    return meetings


#
# Download
#


def is_downloadable(rfile: RecordingFile) -> bool:
    #FILE_TYPES = {FileType.MP4, FileType.M4A, FileType.CHAT}
    FILE_TYPES = {FileType.M4A, FileType.CHAT}

    return (
        rfile.file_type in FILE_TYPES
        and rfile.status == 'completed'
        and rfile.download_url
    )


def make_meeting_dir(prefix: str, meeting: Meeting) -> tp.Optional[str]:
    name = '{} {} {}'.format(
        meeting.start_time,
        meeting.topic,
        meeting.id,
    )
    if name.count('/') > 0:
        raise ValueError('Bad subdir name: {name}')
    else:
        path = os.path.join(prefix, name)

    os.mkdir(path)
    return path


def download_recording_file(prefix: str, rfile: RecordingFile) -> None:
    redirect = requests.get(rfile.download_url, allow_redirects=False)

    status = redirect.status_code
    if not (300 <= status and status < 400):
        raise RuntimeError(f'Expected redirect for {rfile.download_url}')

    redirect_url = redirect.headers['Location']
    redirect_url_path = urllib.parse.urlparse(redirect_url).path
    filename = os.path.basename(redirect_url_path)

    cmdline = ['curl', '-s', redirect_url, '-o', filename]
    subprocess.check_call(cmdline, cwd=prefix)


def download_meeting_recording(prefix: str, meeting: Meeting) -> str:
    files = list(filter(is_downloadable, meeting.recording_files))
    if len(files) == 0:
        return 'No downloadable files'

    try:
        subdir = make_meeting_dir(prefix, meeting)
    except FileExistsError:
        return 'Already downloaded'

    for rfile in files:
        download_recording_file(subdir, rfile)

    return f'Fetched {len(files)} files'
