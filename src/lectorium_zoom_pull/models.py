import datetime
import typing as tp
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, validator


class FileType(str, Enum):
    MP4 = 'MP4'
    M4A = 'M4A'
    TIMELINE = 'TIMELINE'
    TRANSCRIPT = 'TRANSCRIPT'
    CHAT = 'CHAT'
    CC = 'CC'
    CSV = 'CSV'


class RecordingFile(BaseModel):
    id: tp.Optional[str]
    meeting_id: str

    recording_start: datetime.datetime
    recording_end: tp.Optional[datetime.datetime]

    file_type: tp.Optional[FileType]
    file_size: tp.Optional[int]
    play_url: tp.Optional[HttpUrl]
    download_url: tp.Optional[HttpUrl]

    status: tp.Optional[str]
    recording_type: tp.Optional[str]

    @validator('recording_end', pre=True)
    def recording_end_fixup_empty_string(cls, v):
        if v == '':
            return None
        else:
            return v

    @validator('file_type', pre=True)
    def file_type_fixup_empty_string(cls, v):
        if v == '':
            return None
        else:
            return v


class Meeting(BaseModel):
    uuid: str
    id: str
    account_id: str
    
    host_id: str
    host_email: str
    topic: str
    
    start_time: datetime.datetime
    duration: int
    
    total_size: int
    type: int
    recording_count: int
    recording_files: tp.List[RecordingFile]


class AccountsRecordingsRequest(BaseModel):
    next_page_token: tp.Optional[str]
    page_size: tp.Optional[int]
    from_date: tp.Optional[datetime.date] = Field(alias='from')
    to_date: tp.Optional[datetime.date] = Field(alias='to')


class AccountsRecordingsResponse(BaseModel):
    from_date: tp.Optional[datetime.date] = Field(alias='from')
    to_date: tp.Optional[datetime.date] = Field(alias='to')
    page_size: int
    total_records: int
    next_page_token: str
    meetings: tp.List[Meeting]
