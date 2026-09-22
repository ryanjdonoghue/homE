"""Deterministic financial and environmental impact of a schedule change.

Turns an hourly load curve plus grid data into concrete numbers — dollars
and pounds of CO2 — so narrate.py has real figures to explain instead of
having to reason about impact from raw curves itself.
"""

# Illustrative lb CO2 per MWh by fuel type (rough US averages by source).
EMISSIONS_LB_PER_MWH = {
    "COL": 2200.0,
    "NG": 900.0,
    "OIL": 1700.0,
    "NUC": 0.0,
    "WAT": 0.0,
    "SUN": 0.0,
    "WND": 0.0,
    "GEO": 90.0,
    "BAT": 0.0,
    "PS": 0.0,
    "OTH": 1000.0,
    "UNK": 1000.0,
}

# Illustrative residential time-of-use rate, $/kWh, one value per hour of day.
RATE_USD_PER_KWH = [
    0.12, 0.12, 0.12, 0.12, 0.12, 0.12,  # 12am-6am: off-peak
    0.14, 0.16, 0.18, 0.18, 0.18, 0.18,  # 6am-12pm: mid-peak
    0.18, 0.18, 0.18, 0.20, 0.28, 0.34,  # 12pm-6pm: rising toward peak
    0.38, 0.38, 0.34, 0.28, 0.20, 0.14,  # 6pm-12am: evening peak
]


def _carbon_intensity_lb_per_kwh(mix: dict) -> float:
    """Weighted-average grid carbon intensity (lb CO2 per kWh) for one hour's fuel mix."""
    total_mwh = sum(mix.values())
    if total_mwh <= 0:
        return 0.0
    total_lb = sum(EMISSIONS_LB_PER_MWH.get(fueltype, 1000.0) * mwh for fueltype, mwh in mix.items())
    return total_lb / total_mwh / 1000.0


def hourly_carbon_intensity(mix_by_hour: dict) -> list[float]:
    """A 24-entry lb-CO2-per-kWh curve, one value per hour of day."""
    return [_carbon_intensity_lb_per_kwh(mix_by_hour.get(hour, {})) for hour in range(24)]


def financial_impact(baseline_kwh_by_hour: list[float], modified_kwh_by_hour: list[float]) -> dict:
    """Dollar cost of each schedule under the illustrative TOU rate, and the savings."""
    baseline_cost = sum(kwh * rate for kwh, rate in zip(baseline_kwh_by_hour, RATE_USD_PER_KWH))
    modified_cost = sum(kwh * rate for kwh, rate in zip(modified_kwh_by_hour, RATE_USD_PER_KWH))
    return {
        "baseline_cost_usd": baseline_cost,
        "modified_cost_usd": modified_cost,
        "savings_usd": baseline_cost - modified_cost,
    }


def environmental_impact(
    baseline_kwh_by_hour: list[float],
    modified_kwh_by_hour: list[float],
    carbon_intensity_lb_per_kwh: list[float],
) -> dict:
    """Pounds of CO2 attributable to each schedule, and the reduction."""
    baseline_lb = sum(kwh * lb for kwh, lb in zip(baseline_kwh_by_hour, carbon_intensity_lb_per_kwh))
    modified_lb = sum(kwh * lb for kwh, lb in zip(modified_kwh_by_hour, carbon_intensity_lb_per_kwh))
    return {
        "baseline_co2_lb": baseline_lb,
        "modified_co2_lb": modified_lb,
        "co2_reduction_lb": baseline_lb - modified_lb,
    }
