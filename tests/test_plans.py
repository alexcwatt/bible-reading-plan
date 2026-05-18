from datetime import date

import pytest

from bible_reading_plan.utils.plans import (
    FIVE_DAY,
    MCHEYNE_FAMILY,
    MCHEYNE_PRIVATE,
    get_plan,
)


def test_get_plan_known_names():
    assert get_plan("five-day") is FIVE_DAY
    assert get_plan("mcheyne-family") is MCHEYNE_FAMILY
    assert get_plan("mcheyne-private") is MCHEYNE_PRIVATE


def test_get_plan_unknown_raises():
    with pytest.raises(ValueError, match="Unknown plan"):
        get_plan("nonexistent")


def test_five_day_plan_metadata():
    assert FIVE_DAY.name == "five-day"
    assert FIVE_DAY.expected_readings == 260
    assert FIVE_DAY.readings_file.endswith("plans/five-day.txt")


def test_mcheyne_plan_metadata():
    assert MCHEYNE_FAMILY.name == "mcheyne-family"
    assert MCHEYNE_FAMILY.expected_readings == 365
    assert MCHEYNE_PRIVATE.name == "mcheyne-private"
    assert MCHEYNE_PRIVATE.expected_readings == 365


def test_five_day_schedule_skips_weekends():
    # Start Mon 2025-01-06; week 1 should be Mon-Fri Jan 6-10.
    start = date(2025, 1, 6)
    dates = FIVE_DAY.schedule_dates(start, count=10)
    assert dates == [
        date(2025, 1, 6),  # Mon W1D1
        date(2025, 1, 7),  # Tue
        date(2025, 1, 8),  # Wed
        date(2025, 1, 9),  # Thu
        date(2025, 1, 10), # Fri
        date(2025, 1, 13), # Mon W2D1 (skip Sat/Sun)
        date(2025, 1, 14),
        date(2025, 1, 15),
        date(2025, 1, 16),
        date(2025, 1, 17),
    ]


def test_mcheyne_schedule_is_daily():
    start = date(2025, 1, 1)
    dates = MCHEYNE_FAMILY.schedule_dates(start, count=10)
    assert dates == [date(2025, 1, i) for i in range(1, 11)]


def test_five_day_episode_id():
    # First reading in plan: W01_D01
    assert FIVE_DAY.episode_id(0) == "W01_D01"
    assert FIVE_DAY.episode_id(4) == "W01_D05"
    assert FIVE_DAY.episode_id(5) == "W02_D01"
    assert FIVE_DAY.episode_id(259) == "W52_D05"


def test_mcheyne_episode_id():
    assert MCHEYNE_FAMILY.episode_id(0) == "D001"
    assert MCHEYNE_FAMILY.episode_id(99) == "D100"
    assert MCHEYNE_FAMILY.episode_id(364) == "D365"


def test_five_day_episode_title_prefix():
    assert FIVE_DAY.episode_title_prefix(0) == "Week 1, Day 1"
    assert FIVE_DAY.episode_title_prefix(5) == "Week 2, Day 1"


def test_mcheyne_episode_title_prefix():
    assert MCHEYNE_FAMILY.episode_title_prefix(0) == "Day 1"
    assert MCHEYNE_PRIVATE.episode_title_prefix(99) == "Day 100"


def test_five_day_intro_speech_prefix():
    """The TTS intro for an episode names its position in the plan."""
    assert FIVE_DAY.intro_speech_prefix(0) == "Week 1, Day 1"


def test_mcheyne_intro_speech_prefix():
    assert MCHEYNE_FAMILY.intro_speech_prefix(0) == "Day 1"


def test_five_day_source_file_is_parseable():
    """Every line of the five-day plan must parse into one or more chapters."""
    from bible_reading_plan.utils.readings import ScriptureReading, readings

    lines = readings(FIVE_DAY)
    assert len(lines) == FIVE_DAY.expected_readings
    for line_no, raw in enumerate(lines, start=1):
        chapters = ScriptureReading(raw).to_chapters()
        assert chapters, f"five-day line {line_no} ({raw!r}) yielded no chapters"
        ScriptureReading(raw).nice_name()
