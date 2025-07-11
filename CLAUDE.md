# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project that automates the Five Day Bible Reading Plan. It has two main functionalities:
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
- Todoist importer: `TODOIST_API_TOKEN=token TODOIST_PROJECT_ID=id todoist-bible-plan`
- Podcast builder: `podcast-bible-plan`

## Architecture

### Core Data Model
The project centers around two main classes in `utils/readings.py`:

- **`ScriptureReading`**: Parses raw reading strings (e.g., "Gen 6-8; Psalm 104; Mark 3") into structured data
  - `to_chapters()`: Converts to individual chapter names for API calls
  - `nice_name()`: Formats for human display
- **`ScheduledReading`**: Combines ScriptureReading with metadata (date, week, day)

The reading plan data comes from `readings.txt` (260 total readings: 52 weeks × 5 days).

### Podcast Architecture
Recent refactoring introduced a modular segment-based approach:

**`PodcastEpisode`** (`utils/podcast_episode.py`) orchestrates episode creation:
- Generates title/description for each episode
- Composes segments in order: intro → chapter announcements with ESV audio
- Uses ffmpeg to concatenate all segments into final MP3

**Segment Types** (`utils/podcast_segments.py`):
- **`PodcastSegment`**: Abstract base class with build/duration/file_path interface
- **`GeneratedSpeechSegment`**: Google TTS for announcements (cached by text hash)
- **`ESVReadingSegment`**: Downloads audio from ESV API (cached by chapter)
- **`BufferSegment`**: Generates silence for pauses between segments

### CLI Applications
- **`cli/importer.py`**: Interactive Todoist integration requiring API token and project ID
- **`cli/podcast_builder.py`**: Builds audio files and RSS feed, requires ESV_API_KEY and GCS_BUCKET environment variables

## Environment Variables

### Required for Todoist Integration
- `TODOIST_API_TOKEN`: Your Todoist API token
- `TODOIST_PROJECT_ID`: Target project ID for tasks

### Required for Podcast Generation
- `ESV_API_KEY`: ESV API key for downloading Bible audio
- `GCS_BUCKET`: Google Cloud Storage bucket for hosting podcast files

## Build Artifacts

The project creates files in `build/` directory:
- `build/readings/`: Final podcast episode MP3s (W01_D01.mp3 format)
- `build/gtts/`: Cached Google TTS files (named by text hash)
- `build/esv_chapters/`: Cached ESV audio files (named by chapter)
- `build/silence-{duration}.mp3`: Generated silence files for various durations

## Dependencies

Key external dependencies:
- `todoist-api-python`: Todoist API client
- `ffmpeg-python`: Audio processing and concatenation
- `gtts`: Google Text-to-Speech
- `requests`: ESV API calls
- `feedgen`: RSS feed generation for podcast

Note: Requires `ffmpeg` system binary for audio processing.
