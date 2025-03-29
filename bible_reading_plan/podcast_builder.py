import os
from datetime import datetime

from bible_reading_plan.readings import readings_with_dates


def main():
    first_monday_string = "2024-12-30"
    first_monday = datetime.strptime(first_monday_string, "%Y-%m-%d")
    all_readings_with_dates = readings_with_dates(first_monday)

    print("Generating readings")
    for reading_and_date in all_readings_with_dates:
        reading, due_date = reading_and_date
        due_string = due_date.strftime("%Y-%m-%d")
        print(f"Read {reading} due {due_string}")
        print(".", end="", flush=True)

    print("\nDone")
