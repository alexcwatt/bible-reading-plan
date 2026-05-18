from datetime import date

from bible_reading_plan.utils.plans import FIVE_DAY
from bible_reading_plan.utils.readings import (
    ScriptureReading,
    apply_psalm_ssml,
    readings,
    readings_with_dates,
)


def test_reading_to_chapters():
    reading = ScriptureReading("Joshua 5-8; Psalm 14; Luke 15")
    expected = ["Joshua 5", "Joshua 6", "Joshua 7", "Joshua 8", "Psalm 14", "Luke 15"]
    assert reading.to_chapters() == expected

    reading = ScriptureReading("1 Samuel 1-2; Psalm 120; Acts 5")
    expected = ["1 Samuel 1", "1 Samuel 2", "Psalm 120", "Acts 5"]
    assert reading.to_chapters() == expected

    reading = ScriptureReading("2 Chr 15-16; 1 Kin 16; Philemon")
    expected = ["2 Chronicles 15", "2 Chronicles 16", "1 Kings 16", "Philemon"]
    assert reading.to_chapters() == expected


def test_reading_to_chapters_with_commas():
    reading = ScriptureReading("Jer 22, 23, 26; Psalm 77; James 2")
    expected = ["Jeremiah 22", "Jeremiah 23", "Jeremiah 26", "Psalm 77", "James 2"]
    assert reading.to_chapters() == expected


def test_reading_to_chapters_for_single_chapter_books():
    reading = ScriptureReading("Obadiah; Jude; Philemon; Psalm 117")
    expected = ["Obadiah", "Jude", "Philemon", "Psalm 117"]
    assert reading.to_chapters() == expected


def test_reading_to_chapters_with_verse_range():
    """Partial-chapter readings (M'Cheyne style) are kept as one entry."""
    reading = ScriptureReading("Luke 1:1-38")
    assert reading.to_chapters() == ["Luke 1:1-38"]

    reading = ScriptureReading("Zechariah 13:2-9")
    assert reading.to_chapters() == ["Zechariah 13:2-9"]


def test_reading_to_chapters_with_chapter_then_partial():
    reading = ScriptureReading("Exodus 11, 12:1-21; Luke 14")
    assert reading.to_chapters() == ["Exodus 11", "Exodus 12:1-21", "Luke 14"]


def test_reading_to_chapters_two_partials():
    reading = ScriptureReading("Isaiah 9:7-21, 10:1-4")
    assert reading.to_chapters() == ["Isaiah 9:7-21", "Isaiah 10:1-4"]


def test_reading_nice_name():
    reading = ScriptureReading("Ps 119")
    expected = "Psalm 119"
    assert reading.nice_name() == expected

    reading = ScriptureReading("Num 5-8; Psalm 100")
    expected = "Numbers 5-8; and Psalm 100"
    assert reading.nice_name() == expected

    reading = ScriptureReading("Josh 5-8; Ps 14; Luk 15")
    expected = "Joshua 5-8; Psalm 14; and Luke 15"
    assert reading.nice_name() == expected


def test_reading_nice_name_with_commas():
    reading = ScriptureReading("Jer 22, 23, 26; Psalm 77; James 2")
    expected = "Jeremiah 22, 23, 26; Psalm 77; and James 2"
    assert reading.nice_name() == expected


def test_reading_nice_name_for_single_chapter_books():
    reading = ScriptureReading("Obadiah; Jude; Philemon; Psalm 117")
    expected = "Obadiah; Jude; Philemon; and Psalm 117"
    assert reading.nice_name() == expected

    reading = ScriptureReading("Zechariah 12-14; Psalm 94; 2 John")
    expected = "Zechariah 12-14; Psalm 94; and 2 John"
    assert reading.nice_name() == expected


def test_apply_psalm_ssml_basic():
    """Test basic Psalm number formatting."""
    result = apply_psalm_ssml("Psalm 104")
    assert result == 'Psalm <say-as interpret-as="cardinal">104</say-as>'


def test_apply_psalm_ssml_removes_chapter():
    """Test that 'chapter' is removed from Psalm references."""
    result = apply_psalm_ssml("Psalm chapter 104")
    assert result == 'Psalm <say-as interpret-as="cardinal">104</say-as>'


def test_apply_psalm_ssml_non_psalm_unchanged():
    """Test that non-Psalm books are unchanged."""
    result = apply_psalm_ssml("Genesis chapter 1")
    assert result == "Genesis chapter 1"


def test_apply_psalm_ssml_range():
    """Test Psalm range formatting."""
    result = apply_psalm_ssml("Psalms 1-2")
    assert result == 'Psalms <say-as interpret-as="cardinal">1</say-as>-<say-as interpret-as="cardinal">2</say-as>'


def test_apply_psalm_ssml_in_mixed_reading():
    """Test Psalm formatting within a mixed reading string."""
    result = apply_psalm_ssml("Genesis 1-3; Psalm 104; and Mark 1")
    assert result == 'Genesis 1-3; Psalm <say-as interpret-as="cardinal">104</say-as>; and Mark 1'


def test_readings_loads_five_day_plan():
    lines = readings(FIVE_DAY)
    assert len(lines) == FIVE_DAY.expected_readings
    assert lines[0] == "Genesis 1-2; Psalm 19; Mark 1"


def test_readings_with_dates_five_day_schedule():
    # Monday, January 6, 2025
    scheduled = readings_with_dates(FIVE_DAY, date(2025, 1, 6))
    assert len(scheduled) == FIVE_DAY.expected_readings

    first = scheduled[0]
    assert first.plan is FIVE_DAY
    assert first.due_date == date(2025, 1, 6)
    assert first.identifier == "W01_D01"
    assert first.title_prefix == "Week 1, Day 1"

    # Week-2 Monday should skip the weekend.
    assert scheduled[5].due_date == date(2025, 1, 13)
    assert scheduled[5].identifier == "W02_D01"
