import logging
import typing as tp

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


def list_records(
    config: Config,
    from_date: str,
    to_date: str,
    topic_contains: tp.List[str]
) -> None:
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


def download_records(
    config: Config,
    from_date: str,
    to_date: str,
    meeting_ids: tp.List[str],
    downloads_dir: str
) -> None:
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
