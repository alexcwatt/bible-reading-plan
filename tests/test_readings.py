from bible_reading_plan.readings import reading_to_chapters


def test_reading_to_chapters():
    reading = "Joshua 5-8; Psalm 14; Luke 15"
    expected = ["Joshua 5", "Joshua 6", "Joshua 7", "Joshua 8", "Psalm 14", "Luke 15"]
    assert reading_to_chapters(reading) == expected
