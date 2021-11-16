import typing as tp

import click

from lectorium_zoom_pull.auth import authorize
from lectorium_zoom_pull.models import Meeting
from lectorium_zoom_pull.meetings import (
    fetch_all_meetings,
    download_meeting_recording,
)


def auth_and_fetch(
    account_id, tokens_file, auth_code,
    from_date, to_date
) -> tp.List[Meeting]:
    tokens = authorize(
        path=tokens_file,
        auth_code=(auth_code or None),
    )
    print('Access token:', '...' + tokens['access_token'][-16:])
    print('Refresh token:', '...' + tokens['refresh_token'][-16:])

    return fetch_all_meetings(
        tokens,
        account_id=account_id,
        from_date=from_date,
        to_date=to_date
    )


@click.group()
def main():
    pass


@main.command('list')
@click.option('--account-id')
@click.option('--tokens-file')
@click.option('--auth-code', default='', help='Provide auth code on first run')
@click.option('--from-date')
@click.option('--to-date')
def list_records(
    account_id, tokens_file, auth_code,
    from_date, to_date
):
    all_meetings = auth_and_fetch(
        account_id, tokens_file, auth_code,
        from_date, to_date
    )
    for idx, meet in enumerate(all_meetings):
        fmt = '{:3} | MeetingID {} | {} | {}'
        line = fmt.format(idx + 1, meet.id, meet.start_time, meet.topic)
        print(line)


@main.command('download')
@click.option('--account-id')
@click.option('--tokens-file')
@click.option('--auth-code', default='', help='Provide auth code on first run')
@click.option('--from-date')
@click.option('--to-date')
@click.option('--prefix')
def download_records(
    account_id, tokens_file, auth_code,
    from_date, to_date,
    prefix
):
    all_meetings = auth_and_fetch(
        account_id, tokens_file, auth_code,
        from_date, to_date
    )
    for idx, meet in enumerate(all_meetings):
        try:
            status = download_meeting_recording(prefix, meet)
        except Exception as e:
            status = f'Unhandled exception: {e}'
        fmt = '{:3} | MeetingID {} | {} | {} | {}'
        line = fmt.format(idx + 1, meet.id, meet.start_time, meet.topic, status)
        print(line)
