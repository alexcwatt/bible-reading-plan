import datetime

from bible_reading_plan.utils.podcast_episode import PodcastEpisode
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
