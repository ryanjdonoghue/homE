"""Find the best schedule windows for a home change.

Searches every start hour for each segment against the data the app already
has: the illustrative time-of-use rate in impact.py and the hourly carbon
curve built from the EIA fuel mix. Each segment keeps its default duration
so the appliance still gets a realistic run time; only the start hour moves.
This is an exhaustive search over the app's own numbers, not a forecast.
"""

from dataclasses import dataclass

from home_changes import ScheduleChange
from impact import environmental_impact, financial_impact
from load_model import Household

# weight=1 optimizes cost only, weight=0 CO2 only.
GOALS = {
    "Cheapest": 1.0,
    "Balanced": 0.5,
    "Cleanest": 0.0,
}


@dataclass
class Option:
    goal: str
    windows: list[tuple[int, int]]
    money: dict
    co2: dict


def _scaled(value: float, values: list[float]) -> float:
    """Position of value between the smallest (0) and largest (1) of values."""
    low, high = min(values), max(values)
    return (value - low) / (high - low) if high - low > 1e-12 else 0.0


def _evaluate(house: Household, change: ScheduleChange, windows: list[tuple[int, int]], carbon_curve: list[float]):
    baseline_curve = house.hourly_load_kw()
    modified_curve = change.apply(house, windows).hourly_load_kw()
    return (
        financial_impact(baseline_curve, modified_curve),
        environmental_impact(baseline_curve, modified_curve, carbon_curve),
    )


def optimize_change(house: Household, change: ScheduleChange, carbon_curve: list[float], weight: float) -> list[tuple[int, int]]:
    """Best (start_hour, duration) per segment for the given cost/CO2 weight.

    Segments draw from separate hours and costs add up, so each is optimized
    independently while the others stay at their defaults.
    """
    windows = [(segment.default_start_hour, segment.default_duration) for segment in change.segments]
    for index, segment in enumerate(change.segments):
        candidates = []
        for start in segment.start_hours(segment.default_duration):
            trial = list(windows)
            trial[index] = (start, segment.default_duration)
            money, co2 = _evaluate(house, change, trial, carbon_curve)
            candidates.append((start, money["modified_cost_usd"], co2["modified_co2_lb"]))
        # Scale each goal across this segment's own candidates (0 = best, 1 = worst), so the
        # weight blends them evenly instead of the larger-swinging goal always winning.
        costs, co2s = [c[1] for c in candidates], [c[2] for c in candidates]
        best_start, best_score = segment.default_start_hour, None
        for start, cost, lb in candidates:
            score = weight * _scaled(cost, costs) + (1 - weight) * _scaled(lb, co2s)
            if best_score is None or score < best_score - 1e-12:
                best_start, best_score = start, score
        windows[index] = (best_start, segment.default_duration)
    return windows


def optimization_options(house: Household, change: ScheduleChange, carbon_curve: list[float]) -> list[Option]:
    """The Cheapest, Balanced and Cleanest schedules with their cost and CO2 impact."""
    options = []
    for goal, weight in GOALS.items():
        windows = optimize_change(house, change, carbon_curve, weight)
        money, co2 = _evaluate(house, change, windows, carbon_curve)
        options.append(Option(goal, windows, money, co2))
    return options
