from datetime import timedelta
import json
import os

import ffmpeg

from .podcast_segments import BufferSegment, ESVReadingSegment, GeneratedSpeechSegment

# Book names that need pronunciation clarification
PRONUNCIATION_MAP = {
    "Job": '<phoneme alphabet="ipa" ph="dʒoʊb">Job</phoneme>',
}


def _create_chapter_announcement_text(chapter_str):
    """
    Transform chapter string to announcement format with SSML pronunciation.
    Uses existing ScriptureReading parsing logic to avoid duplication.
    """
    from .readings import ScriptureReading, apply_psalm_ssml

    # Reuse existing parsing logic
    reading = ScriptureReading("")
    book_part, chapter_part = reading._book_and_chapter_parts(chapter_str)

    # Apply pronunciation correction
    book_name = PRONUNCIATION_MAP.get(book_part, book_part)

    # Build announcement
    if chapter_part:
        announcement_text = f"{book_name} chapter {chapter_part}"
    else:
        announcement_text = book_name

    # Apply Psalm-specific SSML formatting (removes "chapter", adds cardinal)
    announcement_text = apply_psalm_ssml(announcement_text)

    return f"<speak>{announcement_text}</speak>"


class PodcastEpisode:
    def __init__(self, scheduled_reading):
        self.scheduled_reading = scheduled_reading

    def title(self):
        return f"Week {self.scheduled_reading.week}, Day {self.scheduled_reading.day}: {self.scheduled_reading.reading_nice_name()}"

    def description(self):
        return "<br>".join(
            f"{self._seconds_to_timestamp(start)} – {title}"
            for start, title in self.chapter_start_times()
        )

    def chapter_start_times(self):
        """Return list of (start_seconds, title) tuples for titled segments."""
        chapter_start_times = []
        total_duration = 0
        for segment in self.segments():
            if segment.title():
                chapter_start_times.append((round(total_duration, 1), segment.title()))
            total_duration += segment.duration()
        return chapter_start_times

    @staticmethod
    def _seconds_to_timestamp(total_seconds):
        """Convert seconds to HH:MM:SS or MM:SS format."""
        td = timedelta(seconds=int(total_seconds))
        hrs, remainder = divmod(td.seconds, 3600)
        mins, secs = divmod(remainder, 60)
        if td.days or hrs:
            return f"{td.days * 24 + hrs:02}:{mins:02}:{secs:02}"
        return f"{mins}:{secs:02}"

    def segments(self):
        reading_ssml = self.scheduled_reading.scripture_reading.nice_name_ssml(wrap_speak=False)
        intro_text = f"<speak>Week {self.scheduled_reading.week}, Day {self.scheduled_reading.day}. Today's reading is {reading_ssml}.</speak>"
        intro_segment = GeneratedSpeechSegment(intro_text)
        segments = [intro_segment]

        buffer_segment = BufferSegment(duration_ms=1000)

        for chapter in self.scheduled_reading.scripture_reading.to_chapters():
            segments.append(buffer_segment)
            announcement_text = _create_chapter_announcement_text(chapter)
            segments.append(GeneratedSpeechSegment(announcement_text, title=chapter))
            segments.append(buffer_segment)
            segments.append(ESVReadingSegment(chapter))

        ending_buffer = BufferSegment(duration_ms=3000)
        segments.append(ending_buffer)
        return segments

    def file_path(self):
        return f"build/readings/W{self.scheduled_reading.week:02d}_D{self.scheduled_reading.day:02d}.mp3"

    def metadata_file_path(self):
        return f"bible_reading_plan/metadata/episodes/W{self.scheduled_reading.week:02d}_D{self.scheduled_reading.day:02d}.json"

    def save_metadata(self):
        """Save episode metadata to JSON file for use without audio files."""
        metadata = {
            "title": self.title(),
            "description": self.description(),
            "chapter_start_times": self.chapter_start_times(),
        }
        os.makedirs(os.path.dirname(self.metadata_file_path()), exist_ok=True)
        with open(self.metadata_file_path(), "w") as f:
            json.dump(metadata, f, indent=2)

    def load_metadata(self):
        """Load episode metadata from JSON file. Returns None if not found."""
        if not os.path.exists(self.metadata_file_path()):
            return None
        with open(self.metadata_file_path(), "r") as f:
            return json.load(f)

    def get_description(self):
        """Get description, preferring cached metadata if available."""
        metadata = self.load_metadata()
        if metadata:
            return metadata["description"]
        return self.description()

    def _convert_segments_to_wav(self, segments, temp_dir):
        import hashlib

        wav_cache_dir = "build/wav_cache"
        os.makedirs(wav_cache_dir, exist_ok=True)

        wav_files = []
        for segment in segments:
            mp3_path = segment.file_path()

            with open(mp3_path, "rb") as f:
                mp3_hash = hashlib.md5(f.read()).hexdigest()

            cached_wav = os.path.join(wav_cache_dir, f"{mp3_hash}.wav")

            if not os.path.exists(cached_wav):
                ffmpeg.input(mp3_path).output(
                    cached_wav, acodec="pcm_s16le", ar="44100", ac=1
                ).run(overwrite_output=True, quiet=True)

            wav_files.append(cached_wav)

        return wav_files

    def _create_concat_file(self, wav_files, concat_file):
        with open(concat_file, "w") as f:
            for wav_file in wav_files:
                f.write(f"file '{os.path.abspath(wav_file)}'\n")

    def _concatenate_wav_to_mp3(self, concat_file, output_file):
        ffmpeg.input(concat_file, format="concat", safe=0).output(
            output_file, acodec="libmp3lame", audio_bitrate="128k", ar="44100"
        ).run(overwrite_output=True, quiet=True)

    def _cleanup_temp_files(self, wav_files, concat_file):
        if os.path.exists(concat_file):
            os.remove(concat_file)

    def build(self, force=False):
        audio_exists = os.path.exists(self.file_path())
        metadata_exists = os.path.exists(self.metadata_file_path())

        # Skip if both audio and metadata exist (unless forced)
        if not force and audio_exists and metadata_exists:
            return False

        # Build audio if needed
        if force or not audio_exists:
            os.makedirs(os.path.dirname(self.file_path()), exist_ok=True)

            segments = self.segments()
            for segment in segments:
                segment.build()

            temp_dir = os.path.dirname(self.file_path())
            concat_file = self.file_path() + ".concat.txt"
            wav_files = []

            try:
                wav_files = self._convert_segments_to_wav(segments, temp_dir)
                self._create_concat_file(wav_files, concat_file)
                self._concatenate_wav_to_mp3(concat_file, self.file_path())
            finally:
                self._cleanup_temp_files(wav_files, concat_file)

        # Save metadata (always, if we got here)
        self.save_metadata()

        return not audio_exists  # Return True if audio was generated
