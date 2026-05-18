from datetime import datetime, timezone
import argparse
import os
import shutil

from dotenv import load_dotenv
from feedgen.feed import FeedGenerator
import yaml

from bible_reading_plan.utils.plans import PLANS, get_plan
from bible_reading_plan.utils.podcast_episode import PodcastEpisode
from bible_reading_plan.utils.readings import plan_readings, readings_with_dates

load_dotenv()


def load_podcast_config():
    with open("podcast_config.yaml", "r") as f:
        return yaml.safe_load(f)


def _plan_config(plan_name):
    config = load_podcast_config()
    plan_config = config.get("plans", {}).get(plan_name)
    if not plan_config:
        raise ValueError(f"Plan {plan_name!r} not found in podcast_config.yaml")
    return plan_config


def get_scheduled_readings_for_year(plan, year):
    plan_config = _plan_config(plan.name)
    year_config = plan_config.get("years", {}).get(year)
    if not year_config:
        raise ValueError(
            f"Year {year} not configured for plan {plan.name!r} in podcast_config.yaml"
        )
    start_date = datetime.strptime(year_config["start_date"], "%Y-%m-%d")
    return readings_with_dates(plan, start_date)


def get_configured_years(plan):
    plan_config = _plan_config(plan.name)
    return sorted(plan_config.get("years", {}).keys())


def build_audio_files(plan, count=None, force=False):
    generated_count = 0
    cached_count = 0

    scheduled_readings = plan_readings(plan)
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


_PLAN_FEED_TITLE = {
    "five-day": "Five Day Bible Reading Plan",
    "mcheyne-family": "M'Cheyne Bible Reading Plan (Family)",
    "mcheyne-private": "M'Cheyne Bible Reading Plan (Private)",
}

_PLAN_FEED_DESCRIPTION = {
    "five-day": "A weekday Bible reading plan podcast",
    "mcheyne-family": "M'Cheyne's daily family-worship Bible reading plan podcast",
    "mcheyne-private": "M'Cheyne's daily private Bible reading plan podcast",
}


def build_podcast_feed(plan, year):
    gcs_bucket = os.environ.get("GCS_BUCKET")
    if not gcs_bucket:
        print("Error: GCS_BUCKET environment variable not set")
        return

    if not os.path.exists("build"):
        os.makedirs("build", exist_ok=True)

    shutil.copy("static/podcast-logo.png", "build/logo.png")

    scheduled_readings = get_scheduled_readings_for_year(plan, year)

    print(f"Generating {plan.name} podcast feed for {year}")
    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title(f"{_PLAN_FEED_TITLE[plan.name]} ({year})")
    fg.link(href=f"https://storage.googleapis.com/{gcs_bucket}/", rel="alternate")
    fg.description(f"{_PLAN_FEED_DESCRIPTION[plan.name]} for {year}.")
    fg.id(f"https://storage.googleapis.com/{gcs_bucket}/podcast-{plan.name}-{year}")
    fg.logo(f"https://storage.googleapis.com/{gcs_bucket}/logo.png")
    for scheduled_reading in scheduled_readings:
        if scheduled_reading.due_date > datetime.now():
            break

        episode = PodcastEpisode(scheduled_reading)

        due_date = scheduled_reading.due_date
        fe = fg.add_entry()
        fe.title(episode.title())
        reading_local_path = episode.file_path()
        # file_path is e.g. build/readings/five-day/W01_D01.mp3 — keep the
        # plan subdirectory in the public URL so feeds don't collide.
        reading_subpath = reading_local_path[len("build/"):]
        url = f"https://storage.googleapis.com/{gcs_bucket}/{reading_subpath}"
        fe.enclosure(url, 0, "audio/mpeg")
        fe.description(episode.get_description())
        due_date = due_date.replace(tzinfo=timezone.utc)
        fe.pubDate(due_date)
        fe.id(url)
        print(".", end="", flush=True)

    feed_filename = f"build/podcast-{plan.name}-{year}.xml"
    fg.rss_file(feed_filename)
    print(f"\nPodcast feed saved to {feed_filename}")


def _add_plan_arg(parser):
    parser.add_argument(
        "--plan",
        choices=sorted(PLANS),
        default="five-day",
        help="Reading plan to use (default: five-day)",
    )


def main():
    parser = argparse.ArgumentParser(
        description="CLI for building Bible reading plan resources."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_audio = subparsers.add_parser(
        "build-audio", help="Build all audio files for the Bible readings."
    )
    _add_plan_arg(parser_audio)
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

    parser_feed = subparsers.add_parser(
        "build-feed", help="Build the podcast XML feed."
    )
    _add_plan_arg(parser_feed)
    year_group = parser_feed.add_mutually_exclusive_group(required=True)
    year_group.add_argument(
        "-y", "--year",
        type=int,
        help="Year to build feed for (must be configured in podcast_config.yaml)"
    )
    year_group.add_argument(
        "--all-years",
        action="store_true",
        help="Build feeds for all configured years for this plan"
    )

    args = parser.parse_args()
    plan = get_plan(args.plan)

    if args.command == "build-audio":
        build_audio_files(plan=plan, count=args.count, force=args.force)
    elif args.command == "build-feed":
        if args.all_years:
            for year in get_configured_years(plan):
                build_podcast_feed(plan, year)
        else:
            build_podcast_feed(plan, args.year)
