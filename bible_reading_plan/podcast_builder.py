from datetime import datetime, timezone
import os

from dotenv import load_dotenv
from feedgen.feed import FeedGenerator

from bible_reading_plan.readings import readings_with_dates, reading_to_chapters
from bible_reading_plan.esv_audio import build_reading_file, reading_file_path

load_dotenv()


def main():
    first_monday_string = "2024-12-30"
    first_monday = datetime.strptime(first_monday_string, "%Y-%m-%d")
    all_readings_with_dates = readings_with_dates(first_monday)

    gcs_bucket = os.environ.get("GCS_BUCKET")
    if not gcs_bucket:
        print("Error: GCS_BUCKET environment variable not set")
        return

    print("Generating readings and podcast feed")
    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title("Five Day Bible Reading Plan")
    fg.link(href=f"https://storage.googleapis.com/{gcs_bucket}/", rel="alternate")
    fg.description("A weekday Bible reading plan podcast.")
    fg.id(f"https://storage.googleapis.com/#{gcs_bucket}")
    for reading_with_date in all_readings_with_dates:
        if reading_with_date.week <= 10:
            print("Skipping readings for week <= 10")
            continue

        if reading_with_date.week > 12:
            print("Skipping readings for week > 12")
            continue

        reading = reading_with_date.reading
        due_date = reading_with_date.due_date
        due_string = due_date.strftime("%Y-%m-%d")
        chapters = reading_to_chapters(reading)
        print(
            f"Reading: {reading}, Due Date: {due_string}, Chapters: {chapters}, Week: {reading_with_date.week}, Day: {reading_with_date.day}"
        )
        build_reading_file(reading_with_date)
        fe = fg.add_entry()
        fe.title(
            f"Week {reading_with_date.week}, Day {reading_with_date.day}: {reading_with_date.reading}"
        )
        reading_local_path = reading_file_path(
            reading_with_date.week, reading_with_date.day
        )
        reading_filename = reading_local_path.split("/")[-1]
        url = f"https://storage.googleapis.com/{gcs_bucket}/readings/{reading_filename}"
        fe.enclosure(url, os.path.getsize(reading_local_path), "audio/mpeg")
        fe.description("Today's reading is " + reading)
        # We might not actually want UTC here
        due_date = due_date.replace(tzinfo=timezone.utc)
        fe.pubDate(due_date)
        fe.id(url)
        print(".", end="", flush=True)

    feed_filename = f"build/podcast.xml"
    fg.rss_file(feed_filename)
    print(f"\nPodcast feed saved to {feed_filename}")

    print("\nDone")
