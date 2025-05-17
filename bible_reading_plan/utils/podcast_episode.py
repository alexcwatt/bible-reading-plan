class PodcastEpisode:
    def __init__(self, scheduled_reading):
        self.scheduled_reading = scheduled_reading

    def title(self):
        return f"Week {self.scheduled_reading.week}, Day {self.scheduled_reading.day}: {self.scheduled_reading.reading_nice_name()}"

    def description(self):
        reading = self.scheduled_reading.scripture_reading.nice_name()
        return f"Today's reading is {reading}"
