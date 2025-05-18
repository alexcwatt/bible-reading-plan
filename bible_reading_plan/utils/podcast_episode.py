from datetime import timedelta
import os

import ffmpeg

from .podcast_segments import BufferSegment, ESVReadingSegment, GeneratedSpeechSegment


class PodcastEpisode:
    def __init__(self, scheduled_reading):
        self.scheduled_reading = scheduled_reading

    def title(self):
        return f"Week {self.scheduled_reading.week}, Day {self.scheduled_reading.day}: {self.scheduled_reading.reading_nice_name()}"

    def description(self):
        def seconds_to_timestamp(total_seconds: int) -> str:
            td = timedelta(seconds=int(total_seconds))
            hrs, remainder = divmod(td.seconds, 3600)
            mins, secs = divmod(remainder, 60)
            if td.days or hrs:
                return f"{td.days * 24 + hrs:02}:{mins:02}:{secs:02}"
            return f"{mins}:{secs:02}"

        return "\n".join(
            f"{seconds_to_timestamp(start)} – {title}"
            for start, title in self.chapter_start_times()
        )

    def chapter_start_times(self):
        chapter_start_times = []
        total_duration = 0
        for segment in self.segments():
            if segment.title():
                chapter_start_times.append([total_duration, segment.title()])
            total_duration += segment.duration()

        return chapter_start_times

    def segments(self):
        intro_text = f"Week {self.scheduled_reading.week}, Day {self.scheduled_reading.day}. Today's reading is {self.scheduled_reading.scripture_reading.nice_name()}."
        intro_segment = GeneratedSpeechSegment(intro_text)
        segments = [intro_segment]

        buffer_segment = BufferSegment(duration_ms=1000)

        for chapter in self.scheduled_reading.scripture_reading.to_chapters():
            segments.append(buffer_segment)
            segments.append(GeneratedSpeechSegment(chapter, has_title=True))
            segments.append(buffer_segment)
            segments.append(ESVReadingSegment(chapter))

        return segments

    def file_path(self):
        return f"build/readings/W{self.scheduled_reading.week:02d}_D{self.scheduled_reading.day:02d}.mp3"

    def build(self, force=False):
        if not force and os.path.exists(self.file_path()):
            return

        os.makedirs(os.path.dirname(self.file_path()), exist_ok=True)

        # Concatenate audio files
        for segment in self.segments():
            segment.build()
        input_files = [ffmpeg.input(segment.file_path()) for segment in self.segments()]
        output = ffmpeg.concat(*input_files, v=0, a=1).output(self.file_path())
        output.run(overwrite_output=True)  # quiet=True)
