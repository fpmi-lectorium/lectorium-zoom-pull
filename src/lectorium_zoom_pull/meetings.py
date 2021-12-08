import json
import logging
import os
import os.path
import re
import subprocess
import urllib.parse
import typing as tp
import datetime

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
from lectorium_zoom_pull.months import RU_MONTHS


REPLACE_IN_PATH = re.compile(r'[<>:"/\|?*]')


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
        raise ValueError(f'API error for uuid {meeting.uuid}, details: {rsp.json()}')
    else:
        raise ValueError(f'Bad status code {rsp.status_code} for uuid {meeting.uuid}')


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


def sanitize_path(path: str) -> str:
    replaced, _replacements = REPLACE_IN_PATH.subn(' ', path)
    return replaced


def meeting_dir_path(prefix: str, meeting: Meeting) -> str:
    def by_month(start_time: datetime.datetime) -> str:
        return '{:%Y.%m} - {}'.format(
            start_time,
            RU_MONTHS[start_time.date().month - 1]
        )

    def by_day(start_time: datetime.datetime) -> str:
        return '{:%Y.%m.%d}'.format(start_time)

    return os.path.join(
        prefix,
        by_month(meeting.start_time),
        by_day(meeting.start_time),
        sanitize_path(f'{meeting.topic} {meeting.id}'),
    )

def download_recording_file(
    config: Config,
    prefix: str,
    meeting: Meeting,
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


def download_meeting_recording(
    config: Config,
    prefix: str,
    meeting: Meeting,
) -> str:
    files = list(filter(is_downloadable, meeting.recording_files))
    if len(files) == 0:
        return 'No downloadable files'

    subdir = meeting_dir_path(prefix, meeting)
    logging.debug('Subdir: %s', subdir)
    try:
        os.makedirs(subdir, exist_ok=False)
    except FileExistsError:
        return 'Already downloaded'

    for rfile in files:
        download_recording_file(config, subdir, meeting, rfile)

    return f'Fetched {len(files)} files'
