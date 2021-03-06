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
from lectorium_zoom_pull.downloads import PathManager
from lectorium_zoom_pull.models import (
    AccountsRecordingsRequest,
    AccountsRecordingsResponse,
    Meeting,
    RecordingFile,
    FileType,
)


def encode_meeting_identifier(id_or_uuid: str) -> str:
    if id_or_uuid.startswith('/') or id_or_uuid.count('//') > 0:
        # As of now, id / uuid must be _double_ urlencoded
        # https://devforum.zoom.us/t/double-encode-meeting-uuids/23729
        single_encoded = urllib.parse.quote_plus(id_or_uuid)
        double_encoded = urllib.parse.quote_plus(single_encoded)
        return double_encoded
    else:
        return id_or_uuid


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
    from_date: tp.Optional[str] = None,
    to_date: tp.Optional[str] = None,
    trash: bool = False,
) -> tp.List[Meeting]:
    meetings = []
    next_page_token = None
    while True:
        request = {
            'page_size': 100,
            'next_page_token': next_page_token,
            'from': from_date,
            'to': to_date,
            'trash': trash,
            'trash_type': 'meeting_recordings' if trash else None,
        }
        request = AccountsRecordingsRequest(**request)

        batch = list_recordings(config, request)
        logging.debug('Page size: %d', batch.page_size)
        logging.info('Total records: %d', batch.total_records)
        meetings.extend(batch.meetings)

        next_page_token = batch.next_page_token
        if not next_page_token:
            break

    return meetings


#
# Delete
#


def trash_meeting_recording(config: Config, meeting: Meeting) -> str:
    BASEURL = 'https://api.zoom.us/v2'

    token = jwt_access_token(config)
    url = '{}/meetings/{}/recordings'.format(
        BASEURL,
        encode_meeting_identifier(meeting.uuid)
    )
    rsp = requests.delete(
        url,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        params={
            'action': 'trash',
        }
    )

    if rsp.status_code == 204:
        return 'Trashed'
    elif rsp.status_code == 200:
        raise ValueError(
            f'API error for uuid {meeting.uuid}, details: {rsp.json()}')
    else:
        raise ValueError(
            'Bad status code {} for uuid {}, details: {}'.format(
                rsp.status_code, meeting.uuid, rsp.text
            )
        )


#
# Restore
#


def restore_meeting_recording(config: Config, meeting: Meeting) -> str:
    BASEURL = 'https://api.zoom.us/v2'

    token = jwt_access_token(config)
    url = '{}/meetings/{}/recordings/status'.format(
        BASEURL,
        encode_meeting_identifier(meeting.uuid)
    )
    rsp = requests.put(
        url,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        json={
            'action': 'recover',
        },
    )

    if rsp.status_code == 204:
        return 'Restored'
    elif rsp.status_code == 200:
        raise ValueError(
            f'API error for uuid {meeting.uuid}, details: {rsp.json()}')
    else:
        raise ValueError(
            'Bad status code {} for uuid {}, details: {}'.format(
                rsp.status_code, meeting.uuid, rsp.text
            )
        )


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


def download_recording_file(
    config: Config,
    prefix: str,
    meeting: Meeting,
    rfile: RecordingFile,
) -> str:
    """Return value: file basename"""
    redirect = requests.get(
        rfile.download_url,
        allow_redirects=False,
        params={
            'access_token': jwt_access_token(config)
        }
    )

    status = redirect.status_code
    if not (300 <= status and status < 400):
        logging.error(
            'Expected redirect for %s: %s %s',
            rfile.download_url, redirect.status_code, redirect.text
        )
        raise RuntimeError(f'Expected redirect for {rfile.download_url}')

    redirect_url = redirect.headers['Location']
    redirect_url_path = urllib.parse.urlparse(redirect_url).path
    filename = os.path.basename(redirect_url_path)
    logging.debug('Filename: %s', filename)

    cmdline = [
        'curl',
        '-#' if config.download_progress else '-s',
        redirect_url,
        '-o',
        filename
    ]
    logging.debug('Command line: %s', cmdline)

    logging.info('Downloading %s / %s', meeting.id, filename)
    subprocess.check_call(cmdline, cwd=prefix)

    return filename


def download_meeting_recording(
    config: Config,
    path_manager: PathManager,
    csv_log: tp.TextIO,
    csv_paths_relative_to: str,
    meeting: Meeting,
) -> str:
    files = list(filter(is_downloadable, meeting.recording_files))
    if len(files) == 0:
        return 'No downloadable files'

    subdir = None
    try:
        subdir = path_manager.mkdir_for(meeting)
        logging.debug('Subdir: %s', subdir)
    except FileExistsError:
        return 'Already downloaded'

    for rfile in files:
        basename = download_recording_file(config, subdir, meeting, rfile)
        abs_path = os.path.join(subdir, basename)
        csv_line = (
            f'{meeting.id}\t' +
            f'{meeting.uuid}\t' +
            f'{meeting.start_time:%Y.%m.%d}\t' +
            f'{meeting.start_time:%H-%M-%S%z}\t' +
            os.path.relpath(abs_path, start=csv_paths_relative_to)
        )
        logging.debug('csv: %s', csv_line)
        print(csv_line, file=csv_log)

    return f'Fetched {len(files)} files'
