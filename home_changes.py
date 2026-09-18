"""Definitions for home changes (lights, EV, water heater).

The household twin from load_model.py already owns efficient assets — LED
lighting, an EV charger, a water heater — each running on the naive
schedule an occupant would default to (charge the car the moment it's
home, reheat water right when it's used, light rooms right at dusk). Each
change here does not swap in different hardware; it reschedules *when*
one of those assets draws its power, moving the same total energy to
different hours to see how the timing shift affects conservation and cost.
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Callable

from load_model import Household

# Hours the naive/default schedules concentrate their draw in.
EV_NAIVE_HOURS = [18, 19, 20, 21]  # plugged in right after the evening commute
WATER_HEATER_PEAK_HOURS = [6, 7, 8, 18, 19]  # reheats right at morning/evening use
LIGHTING_PEAK_HOURS = [18, 19, 20, 21]  # on right at evening system peak

# Hours a rescheduled asset can be moved to instead.
OVERNIGHT_OFFPEAK_HOURS = [23, 0, 1, 2, 3, 4]
LIGHTING_OFFPEAK_HOURS = [17, 22]  # dusk/dawn-adjacent, still useful light


@dataclass
class HomeChange:
    """A named schedule change that can be applied to a Household twin."""

    name: str
    description: str
    apply: Callable[[Household], Household]


def _redistribute(hourly_kw: list[float], from_hours: list[int], to_hours: list[int]) -> list[float]:
    """Move all draw during from_hours onto to_hours, preserving total energy."""
    shifted = list(hourly_kw)
    moved = sum(shifted[hour] for hour in from_hours)
    for hour in from_hours:
        shifted[hour] = 0.0
    share = moved / len(to_hours)
    for hour in to_hours:
        shifted[hour] += share
    return shifted


def _reschedule(house: Household, appliance_name: str, from_hours: list[int], to_hours: list[int]) -> Household:
    """Return a copy of house with one appliance's draw moved to new hours."""
    twin = deepcopy(house)
    for appliance in twin.appliances:
        if appliance.name == appliance_name:
            appliance.hourly_kw = _redistribute(appliance.hourly_kw, from_hours, to_hours)
    return twin


def shift_ev_charging_to_overnight(house: Household) -> Household:
    """Delay EV charging from right-after-work to overnight off-peak hours."""
    return _reschedule(house, "ev_charger", EV_NAIVE_HOURS, OVERNIGHT_OFFPEAK_HOURS)


def shift_water_heater_to_offpeak(house: Household) -> Household:
    """Use a timer so the water heater pre-heats overnight instead of
    reheating right at morning/evening peak usage times."""
    return _reschedule(house, "water_heater", WATER_HEATER_PEAK_HOURS, OVERNIGHT_OFFPEAK_HOURS)


def shift_lighting_off_peak(house: Household) -> Household:
    """Use dusk/occupancy-based smart lighting to trim exact-peak-hour
    usage, spreading the same light-hours slightly earlier and later."""
    return _reschedule(house, "lighting", LIGHTING_PEAK_HOURS, LIGHTING_OFFPEAK_HOURS)


CHANGES = [
    HomeChange(
        name="Shift EV charging to overnight",
        description="Delay EV charging from right after the evening commute to overnight off-peak hours.",
        apply=shift_ev_charging_to_overnight,
    ),
    HomeChange(
        name="Shift water heater to off-peak",
        description="Use a timer to pre-heat water overnight instead of reheating at peak usage times.",
        apply=shift_water_heater_to_offpeak,
    ),
    HomeChange(
        name="Shift lighting off peak",
        description="Use dusk/occupancy-based smart lighting to move evening-peak usage slightly earlier and later.",
        apply=shift_lighting_off_peak,
    ),
]
