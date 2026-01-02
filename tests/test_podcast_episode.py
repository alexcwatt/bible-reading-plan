import datetime
import os
import unittest.mock as mock

import pytest

from bible_reading_plan.utils.podcast_episode import PodcastEpisode, _create_chapter_announcement_text
from bible_reading_plan.utils.readings import ScheduledReading

scheduled_reading = ScheduledReading(
    "Gen 6-8; Psalm 104; Mark 3", datetime.date(2025, 1, 1), 1, 3
)


def test_podcast_episode_title():
    episode = PodcastEpisode(scheduled_reading)
    assert episode.title() == "Week 1, Day 3: Genesis 6-8; Psalm 104; and Mark 3"


def test_podcast_episode_description():
    """Test that description formats timestamps correctly."""
    episode = PodcastEpisode(scheduled_reading)

    # Mock the segments to return predictable durations
    class MockSegment:
        def __init__(self, duration_val, title_val=None):
            self._duration = duration_val
            self._title = title_val

        def duration(self):
            return self._duration

        def title(self):
            return self._title

    mock_segments = [
        MockSegment(5.0),  # intro
        MockSegment(1.0),  # buffer
        MockSegment(2.0, "Genesis 6"),  # announcement with title
        MockSegment(1.0),  # buffer
        MockSegment(180.0),  # ESV audio
        MockSegment(1.0),  # buffer
        MockSegment(2.0, "Genesis 7"),  # announcement with title
        MockSegment(1.0),  # buffer
        MockSegment(200.0),  # ESV audio
    ]

    with mock.patch.object(episode, 'segments', return_value=mock_segments):
        description = episode.description()
        lines = description.split('<br>')
        assert len(lines) == 2
        # Genesis 6 starts at: 5 (intro) + 1 (buffer) = 6 seconds
        assert lines[0] == "0:06 – Genesis 6"
        # Genesis 7 starts at: 5+1+2+1+180+1 = 190 seconds = 3:10
        assert lines[1] == "3:10 – Genesis 7"


def test_create_chapter_announcement_text_with_chapter():
    """Test chapter announcement for books with chapter numbers."""
    result = _create_chapter_announcement_text("Genesis 6")
    assert result == "<speak>Genesis chapter 6</speak>"


def test_create_chapter_announcement_text_job_pronunciation():
    """Test that Job gets proper pronunciation tags."""
    result = _create_chapter_announcement_text("Job 30")
    expected = '<speak><phoneme alphabet="ipa" ph="dʒoʊb">Job</phoneme> chapter 30</speak>'
    assert result == expected


def test_create_chapter_announcement_text_mark():
    """Test that Mark is formatted normally (no special pronunciation needed)."""
    result = _create_chapter_announcement_text("Mark 3")
    assert result == "<speak>Mark chapter 3</speak>"


def test_create_chapter_announcement_text_single_book():
    """Test single book names without chapters."""
    result = _create_chapter_announcement_text("Philemon")
    assert result == "<speak>Philemon</speak>"


def test_create_chapter_announcement_text_numbered_book():
    """Test books with numbers in the name."""
    result = _create_chapter_announcement_text("1 Kings 8")
    assert result == "<speak>1 Kings chapter 8</speak>"


def test_create_chapter_announcement_text_multi_word_book():
    """Test multi-word book names."""
    result = _create_chapter_announcement_text("Song of Solomon 2")
    assert result == "<speak>Song of Solomon chapter 2</speak>"


def test_create_chapter_announcement_text_psalm():
    """Test Psalm formatting."""
    result = _create_chapter_announcement_text("Psalm 104")
    assert result == '<speak>Psalm <say-as interpret-as="cardinal">104</say-as></speak>'


class TestSecondsToTimestamp:
    """Tests for _seconds_to_timestamp static method."""

    def test_seconds_only(self):
        assert PodcastEpisode._seconds_to_timestamp(0) == "0:00"
        assert PodcastEpisode._seconds_to_timestamp(30) == "0:30"
        assert PodcastEpisode._seconds_to_timestamp(59) == "0:59"

    def test_minutes_and_seconds(self):
        assert PodcastEpisode._seconds_to_timestamp(60) == "1:00"
        assert PodcastEpisode._seconds_to_timestamp(90) == "1:30"
        assert PodcastEpisode._seconds_to_timestamp(125) == "2:05"
        assert PodcastEpisode._seconds_to_timestamp(599) == "9:59"

    def test_hours(self):
        assert PodcastEpisode._seconds_to_timestamp(3600) == "01:00:00"
        assert PodcastEpisode._seconds_to_timestamp(3661) == "01:01:01"
        assert PodcastEpisode._seconds_to_timestamp(7200) == "02:00:00"

    def test_truncates_decimal(self):
        assert PodcastEpisode._seconds_to_timestamp(90.7) == "1:30"
        assert PodcastEpisode._seconds_to_timestamp(90.2) == "1:30"


class TestChapterStartTimes:
    """Tests for chapter_start_times method."""

    def test_returns_empty_list_when_no_titled_segments(self):
        episode = PodcastEpisode(scheduled_reading)

        class MockSegment:
            def duration(self):
                return 10.0

            def title(self):
                return None

        with mock.patch.object(episode, 'segments', return_value=[MockSegment(), MockSegment()]):
            assert episode.chapter_start_times() == []

    def test_accumulates_durations_correctly(self):
        episode = PodcastEpisode(scheduled_reading)

        class MockSegment:
            def __init__(self, duration_val, title_val=None):
                self._duration = duration_val
                self._title = title_val

            def duration(self):
                return self._duration

            def title(self):
                return self._title

        mock_segments = [
            MockSegment(10.0),  # no title
            MockSegment(5.0, "Chapter A"),  # title at 10s
            MockSegment(20.0),  # no title
            MockSegment(3.0, "Chapter B"),  # title at 35s
        ]

        with mock.patch.object(episode, 'segments', return_value=mock_segments):
            result = episode.chapter_start_times()
            assert result == [(10.0, "Chapter A"), (35.0, "Chapter B")]


class TestSegmentsTitles:
    """Tests that segments() correctly assigns titles."""

    def test_segments_have_titles_for_chapter_announcements(self):
        episode = PodcastEpisode(scheduled_reading)
        segments = episode.segments()

        titled_segments = [s for s in segments if s.title() is not None]
        titles = [s.title() for s in titled_segments]

        # Should have titles for each chapter in the reading
        expected_chapters = scheduled_reading.scripture_reading.to_chapters()
        assert titles == expected_chapters


class TestMetadata:
    """Tests for episode metadata save/load functionality."""

    def test_metadata_file_path(self):
        episode = PodcastEpisode(scheduled_reading)
        assert episode.metadata_file_path() == "bible_reading_plan/metadata/episodes/W01_D03.json"

    def test_save_and_load_metadata(self, tmp_path):
        episode = PodcastEpisode(scheduled_reading)

        # Mock segments to avoid needing audio files
        class MockSegment:
            def __init__(self, duration_val, title_val=None):
                self._duration = duration_val
                self._title = title_val

            def duration(self):
                return self._duration

            def title(self):
                return self._title

        mock_segments = [
            MockSegment(5.0),
            MockSegment(1.0),
            MockSegment(2.0, "Genesis 6"),
            MockSegment(1.0),
            MockSegment(180.0),
        ]

        with mock.patch.object(episode, 'segments', return_value=mock_segments), \
             mock.patch.object(episode, 'metadata_file_path', return_value=str(tmp_path / "test.json")):

            episode.save_metadata()
            metadata = episode.load_metadata()

            assert metadata is not None
            assert metadata["title"] == episode.title()
            assert metadata["description"] == "0:06 – Genesis 6"
            assert metadata["chapter_start_times"] == [[6.0, "Genesis 6"]]

    def test_load_metadata_returns_none_when_file_missing(self, tmp_path):
        episode = PodcastEpisode(scheduled_reading)

        with mock.patch.object(episode, 'metadata_file_path', return_value=str(tmp_path / "nonexistent.json")):
            assert episode.load_metadata() is None

    def test_get_description_uses_cached_metadata(self, tmp_path):
        episode = PodcastEpisode(scheduled_reading)
        metadata_path = tmp_path / "test.json"

        # Write fake metadata
        import json
        with open(metadata_path, "w") as f:
            json.dump({"description": "Cached description"}, f)

        with mock.patch.object(episode, 'metadata_file_path', return_value=str(metadata_path)):
            assert episode.get_description() == "Cached description"

    def test_get_description_falls_back_to_computed(self):
        episode = PodcastEpisode(scheduled_reading)

        class MockSegment:
            def __init__(self, duration_val, title_val=None):
                self._duration = duration_val
                self._title = title_val

            def duration(self):
                return self._duration

            def title(self):
                return self._title

        mock_segments = [
            MockSegment(5.0),
            MockSegment(2.0, "Genesis 6"),
        ]

        with mock.patch.object(episode, 'load_metadata', return_value=None), \
             mock.patch.object(episode, 'segments', return_value=mock_segments):
            assert episode.get_description() == "0:05 – Genesis 6"


class TestMetadataFilesExist:
    """Test that all expected metadata files are committed to the repo."""

    TOTAL_WEEKS = 52
    DAYS_PER_WEEK = 5

    def test_all_metadata_files_exist(self):
        """Verify all 260 episode metadata files exist.

        If this test fails, run: podcast-bible-plan build-audio
        to generate the missing metadata files, then commit them.
        """
        missing_files = []
        metadata_dir = "bible_reading_plan/metadata/episodes"

        for week in range(1, self.TOTAL_WEEKS + 1):
            for day in range(1, self.DAYS_PER_WEEK + 1):
                filename = f"W{week:02d}_D{day:02d}.json"
                filepath = os.path.join(metadata_dir, filename)
                if not os.path.exists(filepath):
                    missing_files.append(filename)

        if missing_files:
            missing_count = len(missing_files)
            sample = missing_files[:5]
            sample_str = ", ".join(sample)
            if missing_count > 5:
                sample_str += f", ... ({missing_count - 5} more)"

            pytest.fail(
                f"Missing {missing_count} metadata file(s): {sample_str}\n\n"
                f"To fix, run: podcast-bible-plan build-audio\n"
                f"Then commit the generated files in {metadata_dir}/"
            )
