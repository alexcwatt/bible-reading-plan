from datetime import timedelta
from collections import namedtuple

from .bible_books import full_book_name_from_abbreviation

WEEKS_IN_YEAR = 52
READINGS_PER_WEEK = 5

Reading = namedtuple("Reading", ["reading", "due_date", "week", "day"])


def readings():
    """
    Reads the readings from the 'readings.txt' file and validates the count.
    """
    with open("readings.txt", "r") as file:
        lines = [line.strip() for line in file]

    expected_readings = WEEKS_IN_YEAR * READINGS_PER_WEEK
    assert (
        len(lines) == expected_readings
    ), f"Incorrect number of readings. Expected {expected_readings}, got {len(lines)}."
    return lines


def readings_with_dates(first_monday):
    """
    Generates a list of Reading objects with their corresponding due dates.
    """
    all_readings = readings()
    readings_with_dates = []

    for week in range(WEEKS_IN_YEAR):
        for day in range(READINGS_PER_WEEK):
            index = week * READINGS_PER_WEEK + day

            reading = all_readings[index]
            date = first_monday + timedelta(weeks=week, days=day)

            readings_with_dates.append(Reading(reading, date, week + 1, day + 1))

    return readings_with_dates


def reading_to_chapters(reading):
    """
    Converts a reading string to a list of chapters.
    """
    chapters = []
    for part in reading.split(";"):
        part = part.strip()

        # Handle cases where the reading is a single chapter book
        if len(part.split(" ")) == 1:
            chapters.append(part)
            continue

        book_part, chapter_part = part.rsplit(" ", 1)
        full_book_name = full_book_name_from_abbreviation(book_part)
        if not full_book_name:
            raise ValueError(f"Invalid book abbreviation: {book_part}")

        if "-" in chapter_part:
            start, end = chapter_part.split("-")
            start = int(start.strip())
            end = int(end.strip())
            chapters.extend(
                [f"{full_book_name} {chapter}" for chapter in range(start, end + 1)]
            )
        else:
            chapters.append(f"{full_book_name} {chapter_part}")

    return chapters
