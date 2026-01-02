from datetime import timedelta
from .bible_books import full_book_name_from_abbreviation

import re

WEEKS_IN_YEAR = 52
READINGS_PER_WEEK = 5


class ScriptureReading:
    """
    Represents the raw Bible reading string and provides methods for processing it.
    """

    def __init__(self, raw_reading):
        self.raw_reading = raw_reading

    def to_chapters(self):
        """
        Converts the raw reading string to a list of chapters.
        """
        chapters = []
        for part in self.raw_reading.split(";"):
            part = part.strip()

            book_part, chapter_part = self._book_and_chapter_parts(part)
            full_book_name = full_book_name_from_abbreviation(book_part)
            if not full_book_name:
                raise ValueError(f"Invalid book abbreviation: {book_part}")

            if chapter_part is None:
                chapters.append(full_book_name)
            elif "-" in chapter_part:
                start, end = chapter_part.split("-")
                start = int(start.strip())
                end = int(end.strip())
                chapters.extend(
                    [f"{full_book_name} {chapter}" for chapter in range(start, end + 1)]
                )
            elif "," in chapter_part:
                for chapter in chapter_part.split(","):
                    chapter = chapter.strip()
                    chapters.append(f"{full_book_name} {chapter}")
            else:
                chapters.append(f"{full_book_name} {chapter_part}")

        return chapters

    def nice_name(self):
        """
        Returns a human-readable name for the reading.
        """
        parts = [part.strip() for part in self.raw_reading.split(";")]
        output = []
        for part in parts:
            book_part, chapter_range_part = self._book_and_chapter_parts(part)
            full_book_name = full_book_name_from_abbreviation(book_part)
            if not full_book_name:
                raise ValueError(f"Invalid book abbreviation: {book_part}")

            output.append(
                f"{full_book_name} {chapter_range_part}"
                if chapter_range_part
                else full_book_name
            )

        if len(output) == 1:
            return output[0]
        else:
            return "; ".join(output[:-1]) + "; and " + output[-1]

    def nice_name_ssml(self, wrap_speak=True):
        """
        Returns an SSML-formatted version of the reading with proper Psalm number handling.
        If wrap_speak is False, returns just the inner content without <speak> tags.
        """
        import re

        nice = self.nice_name()

        def replace_psalm(match):
            psalm_word = match.group(1)
            number = match.group(2)
            return f'{psalm_word} <say-as interpret-as="cardinal">{number}</say-as>'

        formatted = re.sub(r'\b(Psalms?)\s+(\d+)', replace_psalm, nice)

        if wrap_speak:
            return f"<speak>{formatted}</speak>"
        return formatted

    def _book_and_chapter_parts(self, passage):
        """
        Splits the passage into book and chapter parts.
        """
        match_chapter_part_begin = re.search(r"\D(\d+)", passage)
        if not match_chapter_part_begin:
            # Must be a book with one chapter
            return passage.strip(), None

        chapter_part_index = match_chapter_part_begin.start()
        book_part, chapter_part = (
            passage[:chapter_part_index],
            passage[chapter_part_index + 1 :],
        )
        return book_part.strip(), chapter_part.strip()


class ScheduledReading:
    """
    Represents a scheduled reading with metadata such as due date, week, and day.
    """

    def __init__(self, scripture_reading, due_date, week, day):
        self.scripture_reading = ScriptureReading(scripture_reading)
        self.due_date = due_date
        self.week = week
        self.day = day

    def __repr__(self):
        return (
            f"ScheduledReading(scripture_reading={self.scripture_reading.raw_reading}, "
            f"due_date={self.due_date}, week={self.week}, day={self.day})"
        )

    def reading_nice_name(self):
        """
        Returns a human-readable name for the reading.
        """
        return self.scripture_reading.nice_name()


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
    Generates a list of ScheduledReading objects with their corresponding due dates.
    """
    all_readings = readings()
    readings_with_dates = []

    for week in range(WEEKS_IN_YEAR):
        for day in range(READINGS_PER_WEEK):
            index = week * READINGS_PER_WEEK + day

            scripture_reading = all_readings[index]
            date = first_monday + timedelta(weeks=week, days=day)

            readings_with_dates.append(
                ScheduledReading(scripture_reading, date, week + 1, day + 1)
            )

    return readings_with_dates
