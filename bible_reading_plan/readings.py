from datetime import datetime, timedelta

WEEKS_IN_YEAR = 52
READINGS_PER_WEEK = 5


def readings():
    with open("readings.txt", "r") as file:
        lines = [line.strip() for line in file]

    expected_readings = WEEKS_IN_YEAR * READINGS_PER_WEEK
    assert (
        len(lines) == expected_readings
    ), f"Incorrect number of readings. Expected {expected_readings}, got {len(lines)}."
    return lines


def readings_with_dates(first_monday):
    all_readings = readings()
    readings_with_dates = []

    for week in range(WEEKS_IN_YEAR):
        for day in range(READINGS_PER_WEEK):
            index = week * READINGS_PER_WEEK + day

            reading = all_readings[index]
            date = first_monday + timedelta(weeks=week, days=day)

            readings_with_dates.append([reading, date])

    return readings_with_dates


def reading_to_chapters(reading):
    """
    Convert a reading string to a list of chapters.
    """
    chapters = []
    for part in reading.split(";"):
        book_part, chapter_part = part.strip().split(" ")
        if "-" in chapter_part:
            start, end = chapter_part.split("-")
            start = int(start.strip())
            end = int(end.strip())
            chapters.extend(
                [f"{book_part} {chapter}" for chapter in range(start, end + 1)]
            )
        else:
            chapters.append(part.strip())

    return chapters
