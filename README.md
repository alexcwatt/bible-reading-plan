# Five Day Bible Reading Plan - Todoist Integration

Read the Bible in a year with the [Five Day Bible Reading Plan](https://www.fivedaybiblereading.com/) and track your progress in [Todoist](https://todoist.com/).

## About

In 2024, I'm trying the Five Day Bible Reading Plan. I like the way that it's somewhat chronological and I've [heard good things](https://www.challies.com/articles/how-ill-be-reading-the-bible-in-2024/) about it. (In 2023, I did a straight-through reading plan.)

The website provides a free PDF with all the readings organized, but I don't want to use a printed piece of paper to track my readings. I prefer to use an app.

Since I use [Todoist](https://todoist.com/) to organize my life in general, I put together a script to import my daily reading schedule into Todoist. This way, I can track my readings from my phone or computer.

If you wanted to use a different digital tool to read the same plan, I expect this code could still be useful to you; I extracted the readings into a text file and have Python code to calculate the date for each reading, assuming that you read Monday-Friday each week. (It's easy enough in Todoist to reschedule readings as needed.)

## Usage

You can use this tool to import the Bible reading schedule into a Todoist project. I suggest creating a new project called "Bible Reading" where all the tasks can be added.

You'll need Python installed to use this tool.

1. Get your [Todoist API token](https://todoist.com/help/articles/find-your-api-token-Jpzx9IIlB)
2. Find the project ID that you want to add the tasks to (this is visible in the URL when browsing projects).
3. Clone this repository: `git clone git@github.com:alexcwatt/bible-reading-plan`
4. Install the package: `pip install -e .`
5. Run the importer to add the reading schedule to Todoist: `TODOIST_API_TOKEN=yourtoken TODOIST_PROJECT_ID=yourprojectid import`
