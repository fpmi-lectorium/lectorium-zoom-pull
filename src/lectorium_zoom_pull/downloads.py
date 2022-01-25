import re
import os
import os.path
from datetime import datetime

from lectorium_zoom_pull.models import Meeting
from lectorium_zoom_pull.months import RU_MONTHS


class PathManager:
    REPLACE_IN_NAMES = re.compile(r'[<>:"/\|?*]')

    def __init__(self, prefix: str):
        self.prefix = prefix

    @classmethod
    def _sanitize(cls, filename: str) -> str:
        replaced, _replacements = cls.REPLACE_IN_NAMES.subn(' ', filename)
        return replaced

    @classmethod
    def _by_month(cls, dt: datetime) -> str:
        return '{:%Y.%m} - {}'.format(
            dt,
            RU_MONTHS[dt.date().month - 1]
        )

    @classmethod
    def _by_day_of_month(cls, dt: datetime) -> str:
        return '{:%Y.%m.%d}'.format(dt)

    def _meeting_dir(self, meeting: Meeting) -> str:
        dir_name = self._sanitize(
            f'{meeting.topic} {meeting.id} {meeting.start_time:%H-%M-%S%z}'
        )
        return os.path.join(
            self.prefix,
            self._by_month(meeting.start_time),
            self._by_day_of_month(meeting.start_time),
            dir_name,
        )

    def is_downloaded(self, meeting: Meeting) -> bool:
        return os.path.isdir(self._meeting_dir(meeting))

    def mkdir_for(self, meeting: Meeting) -> str:
        """Throws FileExistsError if `self.is_downloaded(meeting)' is true"""
        path = self._meeting_dir(meeting)
        os.makedirs(path)
        return path
