from datetime import datetime, timezone
import argparse
import os
import shutil

from dotenv import load_dotenv
from feedgen.feed import FeedGenerator
import yaml

from bible_reading_plan.utils.podcast_episode import PodcastEpisode
from bible_reading_plan.utils.readings import readings_with_dates

load_dotenv()


def load_podcast_config():
    with open("podcast_config.yaml", "r") as f:
        return yaml.safe_load(f)


def get_scheduled_readings_for_year(year):
    config = load_podcast_config()
    year_config = config["years"].get(year)
    if not year_config:
        raise ValueError(f"Year {year} not found in podcast_config.yaml")
    start_date = datetime.strptime(year_config["start_date"], "%Y-%m-%d")
    return readings_with_dates(start_date)


def get_configured_years():
    config = load_podcast_config()
    return sorted(config["years"].keys())


def build_audio_files(year, count=None, force=False):
    generated_count = 0
    cached_count = 0

    scheduled_readings = get_scheduled_readings_for_year(year)
    readings_to_build = scheduled_readings[:count] if count else scheduled_readings

    for scheduled_reading in readings_to_build:
        podcast_episode = PodcastEpisode(scheduled_reading)
        was_generated = podcast_episode.build(force=force)

        if was_generated:
            print("*", end="", flush=True)
            generated_count += 1
        else:
            print(".", end="", flush=True)
            cached_count += 1

    total = len(readings_to_build)
    print(f"\n\nBuild complete: {generated_count} generated, {cached_count} cached (total: {total})")


def build_podcast_feed(year):
    gcs_bucket = os.environ.get("GCS_BUCKET")
    if not gcs_bucket:
        print("Error: GCS_BUCKET environment variable not set")
        return

    if not os.path.exists("build"):
        os.makedirs("build", exist_ok=True)

    shutil.copy("static/podcast-logo.png", "build/logo.png")

    scheduled_readings = get_scheduled_readings_for_year(year)

    print(f"Generating podcast feed for {year}")
    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title(f"Five Day Bible Reading Plan ({year})")
    fg.link(href=f"https://storage.googleapis.com/{gcs_bucket}/", rel="alternate")
    fg.description(f"A weekday Bible reading plan podcast for {year}.")
    fg.id(f"https://storage.googleapis.com/{gcs_bucket}/podcast-{year}")
    fg.logo(f"https://storage.googleapis.com/{gcs_bucket}/logo.png")
    for scheduled_reading in scheduled_readings:
        if scheduled_reading.due_date > datetime.now():
            break

        episode = PodcastEpisode(scheduled_reading)

        due_date = scheduled_reading.due_date
        fe = fg.add_entry()
        fe.title(episode.title())
        reading_local_path = episode.file_path()
        reading_filename = reading_local_path.split("/")[-1]
        url = f"https://storage.googleapis.com/{gcs_bucket}/readings/{reading_filename}"
        fe.enclosure(url, 0, "audio/mpeg")
        fe.description(episode.get_description())
        due_date = due_date.replace(tzinfo=timezone.utc)
        fe.pubDate(due_date)
        fe.id(url)
        print(".", end="", flush=True)

    feed_filename = f"build/podcast-{year}.xml"
    fg.rss_file(feed_filename)
    print(f"\nPodcast feed saved to {feed_filename}")


def main():
    parser = argparse.ArgumentParser(
        description="CLI for building Bible reading plan resources."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand for building all audio files
    parser_audio = subparsers.add_parser(
        "build-audio", help="Build all audio files for the Bible readings."
    )
    parser_audio.add_argument(
        "-y", "--year",
        type=int,
        required=True,
        help="Year to build audio files for (must be configured in podcast_config.yaml)"
    )
    parser_audio.add_argument(
        "-n", "--count",
        type=int,
        metavar="N",
        help="Number of episodes to build (default: all)"
    )
    parser_audio.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force regeneration of episodes even if they already exist"
    )

    # Subcommand for building the podcast feed
    parser_feed = subparsers.add_parser(
        "build-feed", help="Build the podcast XML feed."
    )
    year_group = parser_feed.add_mutually_exclusive_group(required=True)
    year_group.add_argument(
        "-y", "--year",
        type=int,
        help="Year to build feed for (must be configured in podcast_config.yaml)"
    )
    year_group.add_argument(
        "--all-years",
        action="store_true",
        help="Build feeds for all configured years"
    )

    args = parser.parse_args()

    if args.command == "build-audio":
        build_audio_files(year=args.year, count=args.count, force=args.force)
    elif args.command == "build-feed":
        if args.all_years:
            for year in get_configured_years():
                build_podcast_feed(year)
        else:
            build_podcast_feed(args.year)
