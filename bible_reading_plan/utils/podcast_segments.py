import hashlib
import os

from google.cloud import texttospeech
import ffmpeg
import requests


class PodcastSegment:
    def build(self, force=False):
        if not force and self.is_built():
            return

        os.makedirs(os.path.dirname(self.file_path()), exist_ok=True)

        self._build()

    def is_built(self):
        return os.path.exists(self.file_path())

    def duration(self):
        raise NotImplementedError

    def file_path(self):
        raise NotImplementedError

    def _build(self):
        raise NotImplementedError

    def _duration_from_file(self):
        metadata = ffmpeg.probe(self.file_path())
        return round(float(metadata["format"]["duration"]), 1)


class BufferSegment(PodcastSegment):
    def __init__(self, duration_ms=1000):
        if not isinstance(duration_ms, int):
            raise ValueError("duration_ms must be an integer")

        self.duration_ms = duration_ms

    def duration(self):
        return self.duration_ms / 1000

    def file_path(self):
        return f"build/silence-{self.duration_ms}.mp3"

    def _build(self):
        ffmpeg.input("anullsrc=r=44100:cl=mono", f="lavfi", t=self.duration()).output(
            self.file_path()
        ).run(overwrite_output=True, quiet=True)


class GeneratedSpeechSegment(PodcastSegment):
    def __init__(self, text):
        self.text = text

    def duration(self):
        self.build()
        return self._duration_from_file()

    def file_path(self):
        text_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()
        return f"build/tts/{text_hash}.mp3"

    def _build(self):
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=self.text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        with open(self.file_path(), "wb") as out:
            out.write(response.audio_content)


class ESVReadingSegment(PodcastSegment):
    class DownloadError(Exception):
        """
        Custom exception for download errors.
        """

    def __init__(self, chapter):
        self.chapter = chapter

    def duration(self):
        self.build()
        return self._duration_from_file()

    def file_path(self):
        filename = self.chapter.replace(" ", "_")
        return f"build/esv_chapters/{filename}.mp3"

    def _build(self):
        api_key = os.getenv("ESV_API_KEY")
        if not api_key:
            raise ValueError("ESV_API_KEY environment variable is not set.")

        chapter_encoded = self.chapter.replace(" ", "+")
        url = f"https://api.esv.org/v3/passage/audio/?q={chapter_encoded}"
        headers = {"Authorization": f"Token {api_key}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # Write the audio data to a file
            with open(self.file_path(), "wb") as f:
                f.write(response.content)

        except requests.exceptions.RequestException as e:
            raise self.DownloadError(
                f"Failed to download audio for {self.chapter}: {e}"
            )
