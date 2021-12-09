import logging
import re
import typing as tp

from lectorium_zoom_pull.config import Config
from lectorium_zoom_pull.models import Meeting
from lectorium_zoom_pull.meetings import (
    fetch_all_meetings,
    download_meeting_recording,
    trash_meeting_recording,
    restore_meeting_recording,
)


class Filter:
    @classmethod
    def meeting_id_in(cls, meeting_ids: tp.Set[str]) -> callable:
        the_filter = lambda meeting: meeting.id in meeting_ids
        return the_filter

    @classmethod
    def topic_contains(cls, substrings: tp.List[str]) -> callable:
        the_filter = lambda meeting: any(
            meeting.topic.count(s) for s in substrings
        )
        return the_filter

    @classmethod
    def topic_regex(cls, expression: str) -> callable:
        matcher = re.compile(expression)
        the_filter = lambda meeting: bool(matcher.search(meeting.topic))
        return the_filter

    @classmethod
    def host_email_contains(cls, substrings: tp.List[str]) -> callable:
        the_filter = lambda meeting: any(
            meeting.host_email.count(s) for s in substrings
        )
        return the_filter

    @classmethod
    def host_email_regex(cls, expression: str) -> callable:
        matcher = re.compile(expression)
        the_filter = lambda meeting: bool(matcher.search(meeting.host_email))
        return the_filter


def list_records(
    config: Config,
    from_date: str,
    to_date: str,
    meeting_filter: tp.Optional[tp.Callable[[Meeting], bool]]
) -> None:
    all_meetings = fetch_all_meetings(
        config,
        from_date=from_date,
        to_date=to_date
    )

    if meeting_filter:
        meetings = filter(meeting_filter, all_meetings)
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
    meeting_filter: tp.Callable[[Meeting], bool],
    downloads_dir: str,
    trash_after_download: bool,
) -> None:
    all_meetings = fetch_all_meetings(
        config,
        from_date=from_date,
        to_date=to_date
    )

    meetings = filter(meeting_filter, all_meetings)

    for idx, meet in enumerate(meetings):
        status = ''
        try:
            status += download_meeting_recording(config, downloads_dir, meet)
            if trash_after_download:
                status += ' / ' + trash_meeting_recording(config, meet)
        except Exception as e:
            logging.exception('Unhandled exception')
            status += f'Unhandled exception: {e}'

        fmt = '{:3} | MeetingID {} | {} | {} | {}'
        line = fmt.format(idx + 1, meet.id, meet.start_time, meet.topic, status)
        print(line)

def restore_trashed_records(
    config: Config,
    meeting_filter: tp.Callable[[Meeting], bool],
) -> None:
    all_meetings = fetch_all_meetings(
        config,
        trash=True
    )
    meetings = filter(meeting_filter, all_meetings)

    for idx, meet in enumerate(meetings):
        status = ''
        try:
            status += restore_meeting_recording(config, meet)
        except Exception as e:
            logging.exception('Unhandled exception')
            status += f'Unhandled exception: {e}'

        fmt = '{:3} | MeetingID {} | {} | {} | {}'
        line = fmt.format(idx + 1, meet.id, meet.start_time, meet.topic, status)
        print(line)
