from .bible_books import full_book_name_from_abbreviation
from .plans import FIVE_DAY

import re


def apply_psalm_ssml(text):
    """
    Applies Psalm-specific formatting for SSML:
    - Removes 'chapter' word (Psalms don't use it)
    - Wraps numbers in cardinal SSML for proper pronunciation

    Transforms "Psalm chapter 104" or "Psalm 104" to
    'Psalm <say-as interpret-as="cardinal">104</say-as>'.

    Also handles ranges like "Psalms 1-2".
    """
    def replace_psalm(match):
        psalm_word = match.group(1)
        first_number = match.group(2)
        second_number = match.group(3)
        result = f'{psalm_word} <say-as interpret-as="cardinal">{first_number}</say-as>'
        if second_number:
            result += f'-<say-as interpret-as="cardinal">{second_number}</say-as>'
        return result

    # Remove "chapter" from Psalm references (Psalms don't use it)
    text = re.sub(r'\b(Psalms?)\s+chapter\s+', r'\1 ', text)
    # Apply cardinal SSML for Psalm numbers (including ranges)
    return re.sub(r'\b(Psalms?)\s+(\d+)(?:-(\d+))?', replace_psalm, text)


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
            elif "," in chapter_part:
                for chapter in chapter_part.split(","):
                    chapters.append(f"{full_book_name} {chapter.strip()}")
            elif ":" in chapter_part:
                # Verse-range reference like "1:1-38" — keep as single entry.
                chapters.append(f"{full_book_name} {chapter_part}")
            elif "-" in chapter_part:
                start, end = chapter_part.split("-")
                start = int(start.strip())
                end = int(end.strip())
                chapters.extend(
                    [f"{full_book_name} {chapter}" for chapter in range(start, end + 1)]
                )
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
        formatted = apply_psalm_ssml(self.nice_name())

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
    Represents a scheduled reading with its plan, due date, and position within the plan.
    """

    def __init__(self, plan, scripture_reading, due_date, index):
        self.plan = plan
        self.scripture_reading = ScriptureReading(scripture_reading)
        self.due_date = due_date
        self.index = index

    def __repr__(self):
        return (
            f"ScheduledReading(plan={self.plan.name}, "
            f"scripture_reading={self.scripture_reading.raw_reading}, "
            f"due_date={self.due_date}, index={self.index})"
        )

    @property
    def identifier(self):
        return self.plan.episode_id(self.index)

    @property
    def title_prefix(self):
        return self.plan.episode_title_prefix(self.index)

    @property
    def intro_speech_prefix(self):
        return self.plan.intro_speech_prefix(self.index)

    def reading_nice_name(self):
        return self.scripture_reading.nice_name()


def readings(plan):
    """
    Reads the readings for a plan and validates the count.
    """
    with open(plan.readings_file, "r") as file:
        lines = [line.strip() for line in file if line.strip()]

    assert len(lines) == plan.expected_readings, (
        f"Incorrect number of readings in {plan.readings_file}. "
        f"Expected {plan.expected_readings}, got {len(lines)}."
    )
    return lines


def readings_with_dates(plan, start_date):
    """
    Generates ScheduledReading objects for a plan starting on start_date.
    """
    all_readings = readings(plan)
    dates = plan.schedule_dates(start_date)
    return [
        ScheduledReading(plan, raw, due_date, index)
        for index, (raw, due_date) in enumerate(zip(all_readings, dates))
    ]
