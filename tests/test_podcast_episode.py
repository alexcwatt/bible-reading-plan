import datetime

from bible_reading_plan.utils.podcast_episode import PodcastEpisode, _create_chapter_announcement_text
from bible_reading_plan.utils.readings import ScheduledReading

scheduled_reading = ScheduledReading(
    "Gen 6-8; Psalm 104; Mark 3", datetime.date(2025, 1, 1), 1, 3
)


def test_podcast_episode_title():
    episode = PodcastEpisode(scheduled_reading)
    assert episode.title() == "Week 1, Day 3: Genesis 6-8; Psalm 104; and Mark 3"


def test_podcast_episode_description():
    episode = PodcastEpisode(scheduled_reading)
    assert (
        episode.description() == "Today's reading is Genesis 6-8; Psalm 104; and Mark 3"
    )


def test_create_chapter_announcement_text_with_chapter():
    """Test chapter announcement for books with chapter numbers."""
    result = _create_chapter_announcement_text("Genesis 6")
    assert result == "<speak>Genesis chapter 6</speak>"


def test_create_chapter_announcement_text_job_pronunciation():
    """Test that Job gets proper pronunciation tags."""
    result = _create_chapter_announcement_text("Job 30")
    expected = '<speak><phoneme alphabet="ipa" ph="dʒoʊb">Job</phoneme> chapter 30</speak>'
    assert result == expected


def test_create_chapter_announcement_text_mark_pronunciation():
    """Test that Mark gets proper pronunciation tags."""
    result = _create_chapter_announcement_text("Mark 3")
    expected = '<speak><phoneme alphabet="ipa" ph="mɑːrk">Mark</phoneme> chapter 3</speak>'
    assert result == expected


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
    assert result == "<speak>Psalm 104</speak>"
