import os

import ffmpeg

from .podcast_segments import BufferSegment, ESVReadingSegment, GeneratedSpeechSegment


def _create_chapter_announcement_text(chapter_str):
    """
    Transform chapter string to announcement format with SSML pronunciation.
    Uses existing ScriptureReading parsing logic to avoid duplication.
    """
    from .readings import ScriptureReading

    # Book names that need pronunciation clarification
    PRONUNCIATION_MAP = {
        "Job": '<phoneme alphabet="ipa" ph="dʒoʊb">Job</phoneme>',
        "Mark": '<phoneme alphabet="ipa" ph="mɑːrk">Mark</phoneme>',
        "Acts": '<phoneme alphabet="ipa" ph="ækts">Acts</phoneme>',
        "Numbers": '<phoneme alphabet="ipa" ph="ˈnʌmbərz">Numbers</phoneme>',
        "Judges": '<phoneme alphabet="ipa" ph="ˈdʒʌdʒəz">Judges</phoneme>',
    }

    # Reuse existing parsing logic
    reading = ScriptureReading("")
    book_part, chapter_part = reading._book_and_chapter_parts(chapter_str)

    # Apply pronunciation correction
    book_text = PRONUNCIATION_MAP.get(book_part, book_part)

    if chapter_part:
        if book_part in ["Psalm", "Psalms"]:
            announcement_text = f'{book_text} <say-as interpret-as="cardinal">{chapter_part}</say-as>'
        else:
            announcement_text = f"{book_text} chapter {chapter_part}"
    else:
        announcement_text = book_text

    return f"<speak>{announcement_text}</speak>"


class PodcastEpisode:
    def __init__(self, scheduled_reading):
        self.scheduled_reading = scheduled_reading

    def title(self):
        return f"Week {self.scheduled_reading.week}, Day {self.scheduled_reading.day}: {self.scheduled_reading.reading_nice_name()}"

    def description(self):
        reading = self.scheduled_reading.scripture_reading.nice_name()
        return f"Today's reading is {reading}"

    def segments(self):
        reading_ssml = self.scheduled_reading.scripture_reading.nice_name_ssml(wrap_speak=False)
        intro_text = f"<speak>Week {self.scheduled_reading.week}, Day {self.scheduled_reading.day}. Today's reading is {reading_ssml}.</speak>"
        intro_segment = GeneratedSpeechSegment(intro_text)
        segments = [intro_segment]

        buffer_segment = BufferSegment(duration_ms=1000)

        for chapter in self.scheduled_reading.scripture_reading.to_chapters():
            segments.append(buffer_segment)
            announcement_text = _create_chapter_announcement_text(chapter)
            segments.append(GeneratedSpeechSegment(announcement_text))
            segments.append(buffer_segment)
            segments.append(ESVReadingSegment(chapter))

        ending_buffer = BufferSegment(duration_ms=3000)
        segments.append(ending_buffer)
        return segments

    def file_path(self):
        return f"build/readings/W{self.scheduled_reading.week:02d}_D{self.scheduled_reading.day:02d}.mp3"

    def _convert_segments_to_wav(self, segments, temp_dir):
        wav_files = []
        for i, segment in enumerate(segments):
            wav_file = os.path.join(temp_dir, f".temp_{i:03d}.wav")
            wav_files.append(wav_file)
            ffmpeg.input(segment.file_path()).output(
                wav_file, acodec="pcm_s16le", ar="44100", ac=1
            ).run(overwrite_output=True, quiet=True)
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
        for wav_file in wav_files:
            if os.path.exists(wav_file):
                os.remove(wav_file)
        if os.path.exists(concat_file):
            os.remove(concat_file)

    def build(self, force=False):
        if not force and os.path.exists(self.file_path()):
            return False

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

        return True
