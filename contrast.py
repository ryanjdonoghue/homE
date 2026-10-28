"""Numbers behind the money-view page: what a money-only framing shows, and what it leaves out.

Takes the Cheapest schedule (what a bill-savings app would recommend) and
reports its dollar savings next to the things that framing hides: total kWh
unchanged, CO2 change, grid carbon intensity of the hours chosen, and how
much cleaner the Cleanest schedule would have been.
"""

from home_changes import ScheduleChange
from impact import RATE_USD_PER_KWH, financial_impact
from load_model import Household
from optimize import optimization_options

DAYS_PER_MONTH = 30
DAYS_PER_YEAR = 365


def _weighted_intensity(load_kwh: list[float], carbon_curve: list[float]) -> float:
    """Average lb CO2 per kWh across the hours this load actually draws power."""
    total = sum(load_kwh)
    return sum(kwh * lb for kwh, lb in zip(load_kwh, carbon_curve)) / total if total else 0.0


def _peak(load_kwh: list[float]) -> tuple[int, float]:
    hour = max(range(len(load_kwh)), key=lambda h: load_kwh[h])
    return hour, load_kwh[hour]


def money_view_summary(house: Household, change: ScheduleChange, carbon_curve: list[float]) -> dict:
    options = {option.goal: option for option in optimization_options(house, change, carbon_curve)}
    cheapest, cleanest = options["Cheapest"], options["Cleanest"]

    baseline_curve = house.hourly_load_kw()
    cheapest_curve = change.apply(house, cheapest.windows).hourly_load_kw()
    peak_hour_before, peak_kw_before = _peak(baseline_curve)
    peak_hour_after, peak_kw_after = _peak(cheapest_curve)

    # Absolute figures cover just the selected asset; the load chart keeps the whole house.
    asset_before = change.asset_curve(house)
    asset_after = change.asset_curve(change.apply(house, cheapest.windows))
    asset_money = financial_impact(asset_before, asset_after)

    daily_savings = cheapest.money["savings_usd"]
    return {
        "windows": cheapest.windows,
        "cleanest_windows": cleanest.windows,
        "baseline_curve": baseline_curve,
        "cheapest_curve": cheapest_curve,
        "baseline_cost_usd": asset_money["baseline_cost_usd"],
        "cheapest_cost_usd": asset_money["modified_cost_usd"],
        "daily_savings_usd": daily_savings,
        "monthly_savings_usd": daily_savings * DAYS_PER_MONTH,
        "annual_savings_usd": daily_savings * DAYS_PER_YEAR,
        "baseline_kwh": sum(asset_before),
        "cheapest_kwh": sum(asset_after),
        "co2_reduction_lb": cheapest.co2["co2_reduction_lb"],
        "extra_co2_vs_cleanest_lb": cleanest.co2["co2_reduction_lb"] - cheapest.co2["co2_reduction_lb"],
        "extra_cost_of_cleanest_usd": daily_savings - cleanest.money["savings_usd"],
        "intensity_before": _weighted_intensity(asset_before, carbon_curve),
        "intensity_after": _weighted_intensity(asset_after, carbon_curve),
        "peak_before": (peak_hour_before, peak_kw_before),
        "peak_after": (peak_hour_after, peak_kw_after),
        "avg_intensity": sum(carbon_curve) / len(carbon_curve),
        "avg_rate": sum(RATE_USD_PER_KWH) / len(RATE_USD_PER_KWH),
    }
