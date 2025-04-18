from bible_reading_plan.readings import ScriptureReading


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
