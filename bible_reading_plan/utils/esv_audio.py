import json
import os
import hashlib

from gtts import gTTS
import ffmpeg
import requests


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
    intro_text = f"Week {reading.week}, Day {reading.day}. Today's reading is {reading.scripture_reading.nice_name()}."
    audio_files.append(generate_or_get_audio(intro_text))

    # Generate a short silent audio file for pauses
    pause_path = "build/silence.mp3"
    if not os.path.exists(pause_path):
        os.makedirs(os.path.dirname(pause_path), exist_ok=True)
        ffmpeg.input("anullsrc=r=44100:cl=mono", f="lavfi", t=1).output(pause_path).run(
            overwrite_output=True, quiet=True
        )

    for chapter in reading.scripture_reading.to_chapters():
        audio_files.append(pause_path)
        audio_files.append(generate_or_get_audio(chapter))
        audio_files.append(pause_path)
        download_audio(chapter)
        record_audio_file_length(chapter)
        audio_files.append(audio_file_path(chapter))

    audio_files.append(pause_path)

    output_path = reading_file_path(reading.week, reading.day)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Concatenate audio files
    input_files = [ffmpeg.input(file) for file in audio_files]
    output = ffmpeg.concat(*input_files, v=0, a=1).output(output_path)
    output.run(overwrite_output=True, quiet=True)


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


def record_audio_file_length(chapter):
    file_path = audio_file_path(chapter)
    metadata = ffmpeg.probe(file_path)
    length = round(float(metadata["format"]["duration"]), 1)
    metadata_file_path = f"bible_reading_plan/metadata/bible_chapter_lengths.json"

    if not os.path.exists(metadata_file_path):
        with open(metadata_file_path, "w") as f:
            json.dump({chapter: length}, f, indent=4)
    else:
        data = json.load(open(metadata_file_path, "r"))
        data[chapter] = length
        with open(metadata_file_path, "w") as f:
            json.dump(data, f, indent=4)


def generate_or_get_audio(text):
    """
    Generate audio for the given text using gTTS, or retrieve it if it already exists.

    Args:
        text (str): The text to convert to speech.

    Returns:
        str: The file path of the generated or existing audio file.
    """
    # Hash the input text to create a unique filename
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    audio_path = f"build/gtts/{text_hash}.mp3"

    # Check if the audio file already exists
    if not os.path.exists(audio_path):
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        tts = gTTS(text, lang="en")
        tts.save(audio_path)

    return audio_path
