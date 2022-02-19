import datetime

import unittest

from lectorium_zoom_pull.commands import Filter, Meeting


class TestMeetingFilters(unittest.TestCase):
    @classmethod
    def make_meeting(cls, **kwargs) -> dict:
        m = {
            'uuid': '',
            'id': '',
            'account_id': '',
            'host_id': '',
            'host_email': '',
            'topic': '',
            'start_time': datetime.datetime.now(),
            'duration': None,
            'total_size': 0,
            'type': 0,
            'recording_count': 0,
            'recording_files': [],
        }
        m.update(kwargs)
        return Meeting(**m)

    @classmethod
    def test_meeting_id_in(cls):
        IDS = set(['id-1', 'id-2', 'another-id'])
        filt = Filter.meeting_id_in(IDS)

        for m_id in IDS:
            meeting = cls.make_meeting(id=m_id)
            assert filt(meeting)
            assert filt(meeting)

        first_meeting = cls.make_meeting(id='id-not-on-list')
        assert not filt(first_meeting)
        assert not filt(first_meeting)

    @classmethod
    def test_topic_contains(cls):
        KEYWORDS = ['pea', 'word', 'High']
        filt = Filter.topic_contains(KEYWORDS)
        neg_filt = lambda meeting: not filt(meeting)

        ALLOWED_TOPICS = ['peanuts', 'keyWORD', 'modern hIgher education']
        for topic in ALLOWED_TOPICS:
            meeting = cls.make_meeting(topic=topic)
            assert filt(meeting)
            assert filt(meeting)
            assert not neg_filt(meeting)
            assert not neg_filt(meeting)

        blocked_meeting = cls.make_meeting(topic='trees in forests')
        assert not filt(blocked_meeting)
        assert not filt(blocked_meeting)
        assert neg_filt(blocked_meeting)
        assert neg_filt(blocked_meeting)
