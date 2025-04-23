from datetime import datetime, timezone
import argparse
import os
import shutil

from dotenv import load_dotenv
from feedgen.feed import FeedGenerator

from bible_reading_plan.utils.readings import readings_with_dates
from bible_reading_plan.utils.esv_audio import build_reading_file, reading_file_path

load_dotenv()

FIRST_MONDAY_STRING = "2024-12-30"
FIRST_MONDAY = datetime.strptime(FIRST_MONDAY_STRING, "%Y-%m-%d")
SCHEDULED_READINGS = readings_with_dates(FIRST_MONDAY)


def build_all_audio_files():
    for scheduled_reading in SCHEDULED_READINGS:
        build_reading_file(scheduled_reading)
        print(".", end="", flush=True)


def build_podcast_feed():
    gcs_bucket = os.environ.get("GCS_BUCKET")
    if not gcs_bucket:
        print("Error: GCS_BUCKET environment variable not set")
        return

    if not os.path.exists("build"):
        os.makedirs("build", exist_ok=True)

    shutil.copy("static/podcast-logo.png", "build/logo.png")

    print("Generating readings and podcast feed")
    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title("Five Day Bible Reading Plan")
    fg.link(href=f"https://storage.googleapis.com/{gcs_bucket}/", rel="alternate")
    fg.description("A weekday Bible reading plan podcast.")
    fg.id(f"https://storage.googleapis.com/{gcs_bucket}")
    fg.logo(f"https://storage.googleapis.com/{gcs_bucket}/logo.png")
    for scheduled_reading in SCHEDULED_READINGS:
        if scheduled_reading.due_date > datetime.now():
            break

        reading = scheduled_reading.scripture_reading.nice_name()
        due_date = scheduled_reading.due_date
        fe = fg.add_entry()
        fe.title(
            f"Week {scheduled_reading.week}, Day {scheduled_reading.day}: {scheduled_reading.reading_nice_name()}"
        )
        reading_local_path = reading_file_path(
            scheduled_reading.week, scheduled_reading.day
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


def main():
    parser = argparse.ArgumentParser(
        description="CLI for building Bible reading plan resources."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand for building all audio files
    parser_audio = subparsers.add_parser(
        "build-audio", help="Build all audio files for the Bible readings."
    )

    # Subcommand for building the podcast feed
    parser_feed = subparsers.add_parser(
        "build-feed", help="Build the podcast XML feed."
    )

    args = parser.parse_args()

    if args.command == "build-audio":
        build_all_audio_files()
    elif args.command == "build-feed":
        build_podcast_feed()
