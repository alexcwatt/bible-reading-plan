import os

from todoist_api_python.api import TodoistAPI

from bible_reading_plan.readings import readings_with_dates

def main():
    todoist_api_token = os.environ.get('TODOIST_API_TOKEN')
    if not todoist_api_token:
        print("Error: TODOIST_API_TOKEN environment variable not set")
        return
    
    project_id = os.environ.get('TODOIST_PROJECT_ID')
    if not project_id:
        print("Error: TODOIST_PROJECT_ID environment variable not set")
        return
    
    api = TodoistAPI(todoist_api_token)

    all_readings_with_dates = readings_with_dates()

    print("Adding readings to Todoist")
    for reading_and_date in all_readings_with_dates:
        reading, due_date = reading_and_date
        due_string = due_date.strftime("%Y-%m-%d")
        api.add_task(content=f"Read {reading}", project_id=project_id, due_string=due_string)
        print(".", end="", flush=True)
    
    print("\nDone")
