from bible_reading_plan.bible_books import full_book_name_from_abbreviation


def test_full_book_name_from_abbreviation():
    assert full_book_name_from_abbreviation("Gen") == "Genesis"
    assert full_book_name_from_abbreviation("Exo") == "Exodus"
    assert full_book_name_from_abbreviation("1 Sam") == "1 Samuel"
    assert full_book_name_from_abbreviation("2 Sam") == "2 Samuel"
