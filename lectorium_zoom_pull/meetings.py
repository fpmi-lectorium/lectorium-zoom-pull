import json
import logging
import os
import os.path
import subprocess
import urllib.parse
import typing as tp

import requests

from lectorium_zoom_pull.auth import jwt_access_token
from lectorium_zoom_pull.config import Config
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
    config: Config,
    request: AccountsRecordingsRequest,
) -> AccountsRecordingsResponse:
    BASEURL = 'https://api.zoom.us/v2'

    token = jwt_access_token(config)
    rsp = requests.get(
        BASEURL + '/accounts/me/recordings',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        params=request.dict(by_alias=True, exclude_defaults=True),
    )

    if rsp.status_code != 200:
        raise ValueError('Bad response {}: {}'.format(
            rsp.status_code, rsp.text
        ))
    return AccountsRecordingsResponse(**json.loads(rsp.text))


def fetch_all_meetings(
    config: Config,
    from_date: str, to_date: str
) -> tp.List[Meeting]:
    meetings = []
    next_page_token = None
    while True:
        request = {
            'page_size': 100,
            'next_page_token': next_page_token,
            'from': from_date,
            'to': to_date,
        }
        request = AccountsRecordingsRequest(**request)

        batch = list_recordings(config, request)
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
    FILE_TYPES = {FileType.MP4, FileType.M4A, FileType.CHAT}

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


def download_recording_file(
    config: Config,
    prefix: str,
    rfile: RecordingFile,
) -> None:
    redirect = requests.get(
        rfile.download_url,
        allow_redirects=False,
        params={
            'access_token': jwt_access_token(config)
        }
    )

    status = redirect.status_code
    if not (300 <= status and status < 400):
        logging.error(redirect.status_code, redirect.text)
        raise RuntimeError(f'Expected redirect for {rfile.download_url}')

    redirect_url = redirect.headers['Location']
    redirect_url_path = urllib.parse.urlparse(redirect_url).path
    filename = os.path.basename(redirect_url_path)

    cmdline = ['curl', '-s', redirect_url, '-o', filename]
    subprocess.check_call(cmdline, cwd=prefix)


def download_meeting_recording(
    config: Config,
    prefix: str,
    meeting: Meeting,
) -> str:
    files = list(filter(is_downloadable, meeting.recording_files))
    if len(files) == 0:
        return 'No downloadable files'

    try:
        subdir = make_meeting_dir(prefix, meeting)
    except FileExistsError:
        return 'Already downloaded'

    for rfile in files:
        download_recording_file(config, subdir, rfile)

    return f'Fetched {len(files)} files'
