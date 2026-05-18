# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project that automates Bible reading plans. It supports three plans (the Five Day Bible Reading Plan and the two tracks of Robert Murray M'Cheyne's Daily Bread) and has two main functionalities:
1. **Todoist Integration**: Imports daily Bible readings into Todoist as tasks
2. **Podcast Generation**: Creates audio podcast episodes for each day's reading using ESV API audio and Google TTS

## Common Commands

### Testing
- Run all tests: `poetry run pytest`
- Run specific test file: `poetry run pytest tests/test_filename.py`
- Run with verbose output: `poetry run pytest -v`
- Alternative using justfile: `just test`

### Package Management
- Install dependencies: `poetry install`
- Add dependency: `poetry add package-name`
- Add dev dependency: `poetry add --group dev package-name`

### CLI Applications
Both CLIs accept `--plan {five-day,mcheyne-family,mcheyne-private}` (default: `five-day`).

- Todoist importer: `TODOIST_API_TOKEN=token TODOIST_PROJECT_ID=id todoist-bible-plan [--plan PLAN]`
- Podcast builder: `podcast-bible-plan {build-audio,build-feed} [--plan PLAN]` (build-feed additionally requires `-y YEAR` or `--all-years`; build-audio doesn't depend on dates)

## Architecture

### Core Data Model
The project centers around three main pieces:

- **`ReadingPlan`** (`utils/plans.py`): Describes a plan — its source file, cadence (`weekdays` for the five-day plan, `daily` for M'Cheyne), expected reading count, and how to format an episode identifier and title (e.g., `W01_D03` vs `D045`). Three instances are defined: `FIVE_DAY`, `MCHEYNE_FAMILY`, `MCHEYNE_PRIVATE`.
- **`ScriptureReading`** (`utils/readings.py`): Parses raw reading strings (e.g., `Gen 6-8; Psalm 104; Mark 3` or `Luke 1:1-38`) into structured data. Handles chapter ranges, comma lists, single-chapter books, and partial-chapter verse references (used by M'Cheyne for long chapters like Luke 1, Psalm 78, Psalm 119).
  - `to_chapters()`: Converts to individual chapter names for API calls
  - `nice_name()`: Formats for human display
- **`ScheduledReading`**: Combines a `ReadingPlan`, a `ScriptureReading`, a due date, and the reading's `index` within the plan. Exposes `identifier` (e.g., `W01_D03`, `D045`) and `title_prefix` derived from the plan.

The reading plan data lives in `plans/`:
- `plans/five-day.txt` — 260 readings (52 weeks × 5 days, Mon–Fri)
- `plans/mcheyne-family.txt` — 365 readings (Family OT + Family NT)
- `plans/mcheyne-private.txt` — 365 readings (Private OT + Private NT)

The M'Cheyne files were generated from the canonical PDF at https://www.mcheyne.info/calendar.pdf via `scripts/extract_mcheyne.py`.

### Podcast Architecture
Recent refactoring introduced a modular segment-based approach:

**`PodcastEpisode`** (`utils/podcast_episode.py`) orchestrates episode creation:
- Generates title/description for each episode
- Composes segments in order: intro → chapter announcements with ESV audio
- Uses ffmpeg to concatenate all segments into final MP3

**Segment Types** (`utils/podcast_segments.py`):
- **`PodcastSegment`**: Abstract base class with build/duration/file_path interface
- **`GeneratedSpeechSegment`**: Google Cloud Text-to-Speech for announcements (cached by text hash)
- **`ESVReadingSegment`**: Downloads audio from ESV API (cached by chapter)
- **`BufferSegment`**: Generates silence for pauses between segments

### CLI Applications
- **`cli/importer.py`**: Interactive Todoist integration requiring API token and project ID. Accepts `--plan` (default `five-day`). Prompts for the start date (a Monday for five-day; any date for M'Cheyne).
- **`cli/podcast_builder.py`**: Builds audio files and RSS feed, requires ESV_API_KEY and GCS_BUCKET environment variables. Accepts `--plan` on both `build-audio` and `build-feed` subcommands.

## Environment Variables

### Required for Todoist Integration
- `TODOIST_API_TOKEN`: Your Todoist API token
- `TODOIST_PROJECT_ID`: Target project ID for tasks

### Required for Podcast Generation
- `ESV_API_KEY`: ESV API key for downloading Bible audio
- `GCS_BUCKET`: Google Cloud Storage bucket for hosting podcast files
- Google Cloud authentication: Set up Application Default Credentials for Text-to-Speech API access (see https://cloud.google.com/docs/authentication/external/set-up-adc)
- `GOOGLE_CLOUD_QUOTA_PROJECT`: The project used for the Text-to-Speech API

## Build Artifacts

The project creates files in `build/` directory:
- `build/readings/{plan}/`: Final podcast episode MP3s, namespaced by plan (e.g., `build/readings/five-day/W01_D01.mp3`, `build/readings/mcheyne-family/D001.mp3`)
- `build/tts/`: Cached Google Cloud TTS files (named by text hash, shared across plans)
- `build/esv_chapters/`: Cached ESV audio files (named by chapter, shared across plans)
- `build/silence-{duration}.mp3`: Generated silence files for various durations
- `build/podcast-{plan}-{year}.xml`: Per-plan, per-year RSS feed

Episode metadata is committed to the repo under `bible_reading_plan/metadata/episodes/{plan}/` so descriptions and chapter timestamps are available without regenerating audio.

## Dependencies

Key external dependencies:
- `todoist-api-python`: Todoist API client
- `ffmpeg-python`: Audio processing and concatenation
- `google-cloud-texttospeech`: Google Cloud Text-to-Speech
- `requests`: ESV API calls
- `feedgen`: RSS feed generation for podcast

Note: Requires `ffmpeg` system binary for audio processing.
