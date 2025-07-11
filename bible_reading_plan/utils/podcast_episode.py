import os

import ffmpeg

from .podcast_segments import BufferSegment, ESVReadingSegment, GeneratedSpeechSegment


class PodcastEpisode:
    def __init__(self, scheduled_reading):
        self.scheduled_reading = scheduled_reading

    def title(self):
        return f"Week {self.scheduled_reading.week}, Day {self.scheduled_reading.day}: {self.scheduled_reading.reading_nice_name()}"

    def description(self):
        reading = self.scheduled_reading.scripture_reading.nice_name()
        return f"Today's reading is {reading}"

    def segments(self):
        intro_text = f"Week {self.scheduled_reading.week}, Day {self.scheduled_reading.day}. Today's reading is {self.scheduled_reading.scripture_reading.nice_name()}."
        intro_segment = GeneratedSpeechSegment(intro_text)
        segments = [intro_segment]

        buffer_segment = BufferSegment(duration_ms=1000)

        for chapter in self.scheduled_reading.scripture_reading.to_chapters():
            segments.append(buffer_segment)
            segments.append(GeneratedSpeechSegment(chapter))
            segments.append(buffer_segment)
            segments.append(ESVReadingSegment(chapter))

        return segments

    def file_path(self):
        return f"build/readings/W{self.scheduled_reading.week:02d}_D{self.scheduled_reading.day:02d}.mp3"

    def build(self, force=False):
        """Build the episode. Returns True if generated, False if cached."""
        if not force and os.path.exists(self.file_path()):
            return False

        os.makedirs(os.path.dirname(self.file_path()), exist_ok=True)

        # Concatenate audio files
        for segment in self.segments():
            segment.build()
        input_files = [ffmpeg.input(segment.file_path()) for segment in self.segments()]
        output = ffmpeg.concat(*input_files, v=0, a=1).output(self.file_path())
        output.run(overwrite_output=True, quiet=True)
        return True
