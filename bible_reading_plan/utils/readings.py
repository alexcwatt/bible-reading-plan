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


# So far, the program is structured with two main paths:
# 1. Build up the audio files as its own thing - intro text, pauses in between, etc.
# 2. Build the podcast XML itself which links to the right audio files

# I want to have a feature where I know the timestamps of the audio file parts
# This means we need to generate some metadata when building the audio files
# Maybe we can save this in a file too - a text file that knows that stuff?

# However, so far, the things have been nicely decoupled. I can run the audio generation
# locally and have my GitHub Action just run the podcast builder part...

# Maybe I will change it to be a little bit different. There are two steps:
# 1. Build up audio files and the podcast descriptions - all of the precomputed stuff
# 2. Build the podcast feed in the moment, by leveraging all the prebuilt done-once stuff

# Over time, I will probably evolve the podcast feed and tweak the audio files etc.
# Maybe I should change things a bit so that the system for building the podcast is append-only,
# adding new episodes, and at some point pruning old ones...

# Another idea is that I can store some metadata from the build process and check it into the repo
# That metadata would include, how long is each reading audio file...


# OK, we should have some data structure for the audio file / podcast episode builder
# It should look like this

# PodcastEpisode
# That will have an array of segments/chapters
# Each chapter will have a duration
# We will use this to (1) compile the final audio file and (2) generate the notes for the episode


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

    # We should have a method in here for the intro


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
