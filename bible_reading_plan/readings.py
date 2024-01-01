from datetime import datetime, timedelta

FIRST_MONDAY = datetime(2024, 1, 1)
WEEKS_IN_YEAR = 52
READINGS_PER_WEEK = 5

def readings():
    with open('readings.txt', 'r') as file:
        lines = [line.strip() for line in file]

    expected_readings = WEEKS_IN_YEAR * READINGS_PER_WEEK
    assert len(lines) == expected_readings, f"Incorrect number of readings. Expected {expected_readings}, got {len(lines)}."
    return lines

def readings_with_dates():
    all_readings = readings()
    readings_with_dates = []

    for week in range(WEEKS_IN_YEAR):
        for day in range(READINGS_PER_WEEK):
            index = week * READINGS_PER_WEEK + day

            reading = all_readings[index]
            date = FIRST_MONDAY + timedelta(weeks=week, days=day)

            readings_with_dates.append([reading, date])

    return readings_with_dates
