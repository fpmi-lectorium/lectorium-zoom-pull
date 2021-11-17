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


pass_config = click.make_pass_decorator(Config)


@click.group()
@click.option('--debug/--no-debug', default=False)
@click.option('--download-progress/--no-download-progress', default=True)
@click.option('--secrets-dir', envvar='LZP_SECRETS_DIR')
@click.pass_context
def main(ctx, debug, download_progress, secrets_dir):
    config = dict()

    if debug is not None:
        config.update(debug=debug)
    if download_progress is not None:
        config.update(download_progress=download_progress)
    if secrets_dir is not None:
        config.update(_secrets_dir=secrets_dir)

    config = Config(**config)

    loglevel = logging.DEBUG if config.debug else logging.INFO
    logging.basicConfig(level=loglevel)

    ctx.obj = config


@main.command('list')
@click.option('--from-date')
@click.option('--to-date')
@click.option('--topic-contains', multiple=True)
@pass_config
def list_records(
    config: Config,
    from_date,
    to_date,
    topic_contains
):
    topic_contains = list(topic_contains)

    all_meetings = fetch_all_meetings(
        config,
        from_date=from_date,
        to_date=to_date
    )

    if topic_contains:
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
@click.option('--from-date')
@click.option('--to-date')
@click.option('--meeting-ids')
@click.option('--downloads-dir')
@pass_config
def download_records(
    config: Config,
    from_date,
    to_date,
    meeting_ids,
    downloads_dir
):
    meeting_ids = set(meeting_ids.split(','))

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
            logging.exception('Unhandled exception')
            status = f'Unhandled exception: {e}'
        fmt = '{:3} | MeetingID {} | {} | {} | {}'
        line = fmt.format(idx + 1, meet.id, meet.start_time, meet.topic, status)
        print(line)
