import os

import requests


class DownloadError(Exception):
    """
    Custom exception for download errors.
    """


def audio_file_path(chapter):
    """
    Convert a chapter string to an audio file path.
    """
    filename = chapter.replace(" ", "_")
    return f"build/esv_audio/{filename}.mp3"


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
