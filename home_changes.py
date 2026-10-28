"""Definitions for home changes (lights, EV, water heater).

The household twin from load_model.py already owns efficient assets — LED
lighting, an EV charger, a water heater — each running on the naive
schedule an occupant would default to (charge the car the moment it's
home, reheat water right when it's used, light rooms right at dusk). A
ScheduleChange does not swap in different hardware; it reschedules *when*
one of those assets draws its power. Lighting and the water heater each
have two independent routines — morning and evening, since the occupant
is out at work during the day — so each can be rescheduled on its own.
"""

from copy import deepcopy
from dataclasses import dataclass

from load_model import HOURS_IN_DAY, Household


MORNING = (0, 12)
EVENING = (12, 24)


def hour_window(start_hour: int, duration: int) -> list[int]:
    """The `duration` hours starting at start_hour, wrapping past midnight."""
    return [(start_hour + offset) % HOURS_IN_DAY for offset in range(duration)]


@dataclass
class ScheduleSegment:
    """One independently-reschedulable routine within an appliance's day
    (e.g. a water heater's separate morning and evening reheats).
    """

    label: str
    naive_hours: list[int]
    default_start_hour: int
    default_duration: int
    # The window a rescheduled run must stay inside (no wrapping): morning
    # routines stay before noon, evening routines after it. None = anywhere.
    period: tuple[int, int] | None = None

    def start_hours(self, duration: int) -> list[int]:
        """Every start hour whose `duration`-hour window fits inside the period."""
        if self.period is None:
            return list(range(HOURS_IN_DAY))
        lo, hi = self.period
        return list(range(lo, hi - duration + 1))

    def max_duration(self, start_hour: int) -> int:
        """Longest window that fits from start_hour without leaving the period."""
        return 12 if self.period is None else self.period[1] - start_hour


@dataclass
class ScheduleChange:
    """A reschedulable asset: one or more routines, each with its own
    naive default hours and a user-chosen target window it can move to.
    """

    name: str
    description: str
    appliance_name: str
    segments: list[ScheduleSegment]

    def asset_curve(self, house: Household) -> list[float]:
        """Hourly kW of just this change's appliance, not the whole house."""
        appliance = next(a for a in house.appliances if a.name == self.appliance_name)
        return list(appliance.hourly_kw)

    def apply(self, house: Household, windows: list[tuple[int, int]]) -> Household:
        """Return a twin with each segment's draw moved to its chosen window.

        `windows` must have one (start_hour, duration) pair per segment, in
        the same order as self.segments.
        """
        twin = deepcopy(house)
        for appliance in twin.appliances:
            if appliance.name != self.appliance_name:
                continue
            original_kw = appliance.hourly_kw
            # Clear every segment's naive hours first, then add each segment's
            # energy to its target window. Doing this per segment in sequence
            # would let a later segment erase energy an earlier one moved onto
            # its naive hours, silently destroying energy.
            hourly_kw = list(original_kw)
            for segment in self.segments:
                for hour in segment.naive_hours:
                    hourly_kw[hour] = 0.0
            for segment, (start_hour, duration) in zip(self.segments, windows):
                target_hours = hour_window(start_hour, duration)
                moved = sum(original_kw[hour] for hour in segment.naive_hours)
                for hour in target_hours:
                    hourly_kw[hour] += moved / len(target_hours)
            appliance.hourly_kw = hourly_kw
        return twin


CHANGES = [
    ScheduleChange(
        name="EV charging",
        description="Move car charging away from right-after-work to a window you choose.",
        appliance_name="ev_charger",
        segments=[
            ScheduleSegment(
                label="Evening charge",
                naive_hours=[18, 19, 20, 21],
                default_start_hour=23,
                default_duration=6,
            ),
        ],
    ),
    ScheduleChange(
        name="Water heater",
        description="Use a timer to pre-heat water in windows you choose instead of reheating at peak usage times.",
        appliance_name="water_heater",
        segments=[
            ScheduleSegment(
                label="Morning routine",
                naive_hours=[6, 7, 8],
                default_start_hour=2,
                default_duration=3,
                period=MORNING,
            ),
            ScheduleSegment(
                label="Evening routine",
                naive_hours=[18, 19],
                default_start_hour=21,
                default_duration=3,
                period=EVENING,
            ),
        ],
    ),
    ScheduleChange(
        name="Lighting",
        description="Use smart lighting to move usage in each routine into a window you choose.",
        appliance_name="lighting",
        segments=[
            ScheduleSegment(
                label="Morning routine",
                naive_hours=[6, 7],
                default_start_hour=5,
                default_duration=2,
                period=MORNING,
            ),
            ScheduleSegment(
                label="Evening routine",
                naive_hours=[18, 19, 20, 21],
                default_start_hour=17,
                default_duration=5,
                period=EVENING,
            ),
        ],
    ),
]
