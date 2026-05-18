from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable


@dataclass(frozen=True)
class ReadingPlan:
    name: str
    readings_file: str
    expected_readings: int
    cadence: str  # "weekdays" or "daily"
    _episode_id: Callable[[int], str]
    _episode_title_prefix: Callable[[int], str]

    def schedule_dates(self, start_date, count=None):
        n = count if count is not None else self.expected_readings
        dates = []
        current = start_date
        while len(dates) < n:
            if self.cadence == "weekdays":
                if current.weekday() < 5:  # Mon=0..Fri=4
                    dates.append(current)
            else:  # daily
                dates.append(current)
            current = current + timedelta(days=1)
        return dates

    def episode_id(self, index):
        return self._episode_id(index)

    def episode_title_prefix(self, index):
        return self._episode_title_prefix(index)

    def intro_speech_prefix(self, index):
        # Same wording as the title prefix; kept as a separate hook so TTS
        # phrasing can diverge from on-screen titles later if needed.
        return self.episode_title_prefix(index)


def _five_day_episode_id(index):
    week = index // 5 + 1
    day = index % 5 + 1
    return f"W{week:02d}_D{day:02d}"


def _five_day_title_prefix(index):
    week = index // 5 + 1
    day = index % 5 + 1
    return f"Week {week}, Day {day}"


def _mcheyne_episode_id(index):
    return f"D{index + 1:03d}"


def _mcheyne_title_prefix(index):
    return f"Day {index + 1}"


FIVE_DAY = ReadingPlan(
    name="five-day",
    readings_file="plans/five-day.txt",
    expected_readings=260,
    cadence="weekdays",
    _episode_id=_five_day_episode_id,
    _episode_title_prefix=_five_day_title_prefix,
)

MCHEYNE_FAMILY = ReadingPlan(
    name="mcheyne-family",
    readings_file="plans/mcheyne-family.txt",
    expected_readings=365,
    cadence="daily",
    _episode_id=_mcheyne_episode_id,
    _episode_title_prefix=_mcheyne_title_prefix,
)

MCHEYNE_PRIVATE = ReadingPlan(
    name="mcheyne-private",
    readings_file="plans/mcheyne-private.txt",
    expected_readings=365,
    cadence="daily",
    _episode_id=_mcheyne_episode_id,
    _episode_title_prefix=_mcheyne_title_prefix,
)


PLANS = {p.name: p for p in (FIVE_DAY, MCHEYNE_FAMILY, MCHEYNE_PRIVATE)}


def get_plan(name):
    if name not in PLANS:
        raise ValueError(f"Unknown plan: {name!r}. Known: {sorted(PLANS)}")
    return PLANS[name]
