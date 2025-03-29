import os
from datetime import datetime

from bible_reading_plan.readings import readings_with_dates, reading_to_chapters
from bible_reading_plan.esv_audio import build_reading_file


def main():
    first_monday_string = "2024-12-30"
    first_monday = datetime.strptime(first_monday_string, "%Y-%m-%d")
    all_readings_with_dates = readings_with_dates(first_monday)

    print("Generating readings")
    for reading_with_date in all_readings_with_dates:
        if reading_with_date.week <= 10:
            print("Skipping readings for week <= 10")
            continue

        reading = reading_with_date.reading
        due_date = reading_with_date.due_date
        due_string = due_date.strftime("%Y-%m-%d")
        chapters = reading_to_chapters(reading)
        print(
            f"Reading: {reading}, Due Date: {due_string}, Chapters: {chapters}, Week: {reading_with_date.week}, Day: {reading_with_date.day}"
        )
        build_reading_file(reading_with_date)
        print(".", end="", flush=True)

    print("\nDone")
