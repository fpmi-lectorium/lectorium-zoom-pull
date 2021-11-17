import logging
import typing as tp

import click

from lectorium_zoom_pull.config import Config
from lectorium_zoom_pull.models import Meeting
from lectorium_zoom_pull.meetings import (
    fetch_all_meetings,
    download_meeting_recording,
)


def filter_topic_contains(substrings: tp.List[str]) -> callable:
    def filter_callable(meeting: Meeting) -> bool:
        return any([meeting.topic.count(s) for s in substrings])

    return filter_callable


def filter_meeting_id_in(meeting_ids: tp.Set[str]) -> callable:
    def filter_callable(meeting: Meeting) -> bool:
        return meeting.id in meeting_ids

    return filter_callable


@click.group()
def main():
    pass


@main.command('list')
@click.option('--secrets-dir')
@click.option('--from-date')
@click.option('--to-date')
@click.option('--topic-contains', multiple=True)
def list_records(
    secrets_dir,
    from_date, to_date,
    topic_contains
):
    topic_contains = list(topic_contains)
    config = Config(
        _secrets_dir=secrets_dir
    )

    all_meetings = fetch_all_meetings(
        config,
        from_date=from_date,
        to_date=to_date
    )

    if topic_contains:
        print('tc', topic_contains)
        meetings = filter(
            filter_topic_contains(topic_contains),
            all_meetings
        )
    else:
        meetings = all_meetings

    for idx, meet in enumerate(meetings):
        fmt = '{:3} | MeetingID {} | {} | {}'
        line = fmt.format(idx + 1, meet.id, meet.start_time, meet.topic)
        print(line)


@main.command('download')
@click.option('--secrets-dir')
@click.option('--from-date')
@click.option('--to-date')
@click.option('--meeting-ids')
@click.option('--downloads-dir')
def download_records(
    secrets_dir,
    from_date, to_date,
    meeting_ids,
    downloads_dir
):
    meeting_ids = set(meeting_ids.split(','))
    config = Config(
        _secrets_dir=secrets_dir
    )

    all_meetings = fetch_all_meetings(
        config,
        from_date=from_date,
        to_date=to_date
    )

    if meeting_ids:
        meetings = filter(
            filter_meeting_id_in(meeting_ids),
            all_meetings
        )
    else:
        meetings = all_meetings

    for idx, meet in enumerate(meetings):
        try:
            status = download_meeting_recording(config, downloads_dir, meet)
        except Exception as e:
            logging.exception('dl failed')
            status = f'Unhandled exception: {e}'
        fmt = '{:3} | MeetingID {} | {} | {} | {}'
        line = fmt.format(idx + 1, meet.id, meet.start_time, meet.topic, status)
        print(line)
