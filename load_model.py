"""Synthetic household load curve generation.

Models a house as a small digital twin: a handful of appliances, each with
its own characteristic hourly draw, combined into one 24-hour household
load curve. The baseline twin already owns efficient assets — LED
lighting, an EV charger, a water heater — each running on the naive
schedule an occupant would use without thinking about grid conditions.
home_changes.py builds on this by rescheduling *when* an existing
appliance draws its power, not by swapping in different hardware.
"""

from dataclasses import dataclass, field

HOURS_IN_DAY = 24


@dataclass
class Appliance:
    """A single household end-use and its characteristic hourly draw (kW)."""

    name: str
    hourly_kw: list[float]

    def __post_init__(self):
        if len(self.hourly_kw) != HOURS_IN_DAY:
            raise ValueError(
                f"{self.name}: expected {HOURS_IN_DAY} hourly values, got {len(self.hourly_kw)}"
            )


@dataclass
class Household:
    """A digital twin of a house: the set of appliances driving its load."""

    appliances: list[Appliance] = field(default_factory=list)

    def add(self, appliance: Appliance) -> None:
        self.appliances.append(appliance)

    def hourly_load_kw(self) -> list[float]:
        """Sum every appliance's draw into one 24-hour household load curve."""
        totals = [0.0] * HOURS_IN_DAY
        for appliance in self.appliances:
            for hour, kw in enumerate(appliance.hourly_kw):
                totals[hour] += kw
        return totals


def baseline_household() -> Household:
    """A house that already has efficient assets — LED lighting, an EV
    charger, and a water heater — each left on its default, unoptimized
    schedule: power drawn whenever the occupant happens to use it, with no
    regard for grid conditions or time-of-use pricing. home_changes.py
    changes when these assets run, not what they are.
    """
    house = Household()
    house.add(Appliance("lighting", _lighting_profile()))
    house.add(Appliance("water_heater", _water_heater_profile()))
    house.add(Appliance("ev_charger", _ev_charger_profile()))
    house.add(Appliance("baseline_plug_load", _baseline_plug_profile()))
    return house


def _lighting_profile() -> list[float]:
    """LEDs, but on a naive schedule: off overnight, a small morning bump,
    a bigger evening peak right when everyone's home.
    """
    return [
        0.05, 0.05, 0.05, 0.05, 0.05, 0.1,  # 12am-6am
        0.3, 0.4, 0.2, 0.1, 0.1, 0.1,  # 6am-12pm
        0.1, 0.1, 0.1, 0.15, 0.3, 0.6,  # 12pm-6pm
        1.0, 1.2, 1.0, 0.6, 0.3, 0.1,  # 6pm-12am
    ]


def _water_heater_profile() -> list[float]:
    """An efficient water heater, but reheating right when it's used —
    morning showers and evening showers/dishwashing.
    """
    return [
        0.2, 0.2, 0.2, 0.2, 0.2, 0.5,
        1.5, 1.8, 1.0, 0.4, 0.3, 0.3,
        0.3, 0.3, 0.3, 0.4, 0.6, 1.2,
        1.8, 1.5, 0.8, 0.4, 0.3, 0.2,
    ]


def _ev_charger_profile() -> list[float]:
    """A Level 2 charger, plugged in the moment the car gets home from the
    evening commute and left to charge until full — the naive default.
    """
    profile = [0.0] * HOURS_IN_DAY
    for hour in (18, 19, 20, 21):
        profile[hour] = 7.2
    return profile


def _baseline_plug_profile() -> list[float]:
    """Refrigeration, standby electronics, etc. — roughly flat all day."""
    return [0.4] * HOURS_IN_DAY
