from bible_reading_plan.readings import reading_to_chapters


def test_reading_to_chapters():
    reading = "Joshua 5-8; Psalm 14; Luke 15"
    expected = ["Joshua 5", "Joshua 6", "Joshua 7", "Joshua 8", "Psalm 14", "Luke 15"]
    assert reading_to_chapters(reading) == expected

    reading = "1 Samuel 1-2; Psalm 120; Acts 5"
    expected = ["1 Samuel 1", "1 Samuel 2", "Psalm 120", "Acts 5"]
    assert reading_to_chapters(reading) == expected

    reading = "2 Chr 15-16; 1 Kin 16; Philemon"
    expected = ["2 Chronicles 15", "2 Chronicles 16", "1 Kings 16", "Philemon"]
    assert reading_to_chapters(reading) == expected
