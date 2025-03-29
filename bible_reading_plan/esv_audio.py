import os

from gtts import gTTS
import ffmpeg
import requests

from bible_reading_plan.readings import reading_to_chapters


class DownloadError(Exception):
    """
    Custom exception for download errors.
    """


def build_reading_file(reading):
    """
    Build the audio file for a given reading.
    """
    audio_files = []

    # Generate the intro
    generate_reading_intro(reading)
    audio_files.append(reading_intro_file_path(reading.week, reading.day))

    for chapter in reading_to_chapters(reading.reading):
        download_audio(chapter)
        audio_files.append(audio_file_path(chapter))

    output_path = reading_file_path(reading.week, reading.day)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Concatenate audio files
    input_files = [ffmpeg.input(file) for file in audio_files]
    output = ffmpeg.concat(*input_files, v=0, a=1).output(output_path)
    output.run(overwrite_output=True, quiet=True)


def reading_intro_file_path(week, day):
    """
    Get the file path for the reading intro.
    """
    return f"build/reading_intros/W{week:02d}_D{day:02d}.mp3"


def generate_reading_intro(reading):
    """
    Generate an intro for the reading.
    """
    intro = (
        f"Week {reading.week}, Day {reading.day}. Today's reading is {reading.reading}."
    )
    tts = gTTS(intro, lang="en")
    audio_path = reading_intro_file_path(reading.week, reading.day)
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    tts.save(audio_path)


def reading_file_path(week, day):
    """
    Get the file path for a given reading.
    """
    return f"build/readings/W{week:02d}_D{day:02d}.mp3"


def audio_file_path(chapter):
    """
    Convert a chapter string to an audio file path.
    """
    filename = chapter.replace(" ", "_")
    return f"build/esv_chapters/{filename}.mp3"


def download_audio(chapter, force=False):
    """
    Download the audio for a given chapter if it doesn't exist.
    """
    api_key = os.getenv("ESV_API_KEY")
    if not api_key:
        raise ValueError("ESV_API_KEY environment variable is not set.")

    audio_path = audio_file_path(chapter)
    if os.path.exists(audio_path) and not force:
        return

    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
    chapter_encoded = chapter.replace(" ", "+")
    url = f"https://api.esv.org/v3/passage/audio/?q={chapter_encoded}"
    headers = {"Authorization": f"Token {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Write the audio data to a file
        with open(audio_path, "wb") as f:
            f.write(response.content)

    except requests.exceptions.RequestException as e:
        raise DownloadError(f"Failed to download audio for {chapter}: {e}")
