import argparse
import os
from datetime import datetime

from todoist_api_python.api import TodoistAPI

from bible_reading_plan.utils.plans import PLANS, get_plan
from bible_reading_plan.utils.readings import readings_with_dates


def main():
    parser = argparse.ArgumentParser(
        description="Import a Bible reading plan into Todoist."
    )
    parser.add_argument(
        "--plan",
        choices=sorted(PLANS),
        default="five-day",
        help="Reading plan to import (default: five-day)",
    )
    args = parser.parse_args()
    plan = get_plan(args.plan)

    todoist_api_token = os.environ.get("TODOIST_API_TOKEN")
    if not todoist_api_token:
        print("Error: TODOIST_API_TOKEN environment variable not set")
        return

    project_id = os.environ.get("TODOIST_PROJECT_ID")
    if not project_id:
        print("Error: TODOIST_PROJECT_ID environment variable not set")
        return

    api = TodoistAPI(todoist_api_token)

    prompt = (
        "Enter the Monday on which you want the reading plan to start (YYYY-MM-DD): "
        if plan.cadence == "weekdays"
        else "Enter the date on which you want the reading plan to start (YYYY-MM-DD): "
    )
    start_date_string = input(prompt)
    start_date = datetime.strptime(start_date_string, "%Y-%m-%d")
    all_readings_with_dates = readings_with_dates(plan, start_date)

    print(f"Adding {plan.name} readings to Todoist")
    for scheduled_reading in all_readings_with_dates:
        due_string = scheduled_reading.due_date.strftime("%Y-%m-%d")
        api.add_task(
            content=f"Read {scheduled_reading.reading_nice_name()}",
            project_id=project_id,
            due_string=due_string,
        )
        print(".", end="", flush=True)

    print("\nDone")
