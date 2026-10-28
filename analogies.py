"""Everyday comparisons for a schedule change's savings.

Rescheduling moves energy use to a different time; it does not reduce total
kWh. So the savings are cost and CO2, and the analogies express those: the
CO2 avoided as miles not driven or as the emissions of running a household
appliance, and the dollars saved as how much appliance use they would pay for.
Constants are rough, round figures for illustration.
"""

CAR_LB_CO2_PER_MILE = 0.88  # ~0.4 kg CO2 per mile, typical gasoline car

# (singular, plural, kWh per unit)
APPLIANCE_USES = [
    ("minute of microwave use", "minutes of microwave use", 1.1 / 60),  # 1.1 kW
    ("washing machine cycle", "washing machine cycles", 0.5),
    ("dryer cycle", "dryer cycles", 3.0),
    ("phone charge", "phone charges", 0.012),
    ("hour of LED bulb light", "hours of LED bulb light", 0.010),  # 10 W
]


def _most_readable(kwh_equivalent: float) -> str:
    """Phrase `kwh_equivalent` in the appliance unit whose count is nearest 10.

    Counts below 1 read badly ("0 cycles"), so they are skipped unless no unit gives >= 1.
    """
    counts = [(single, plural, kwh_equivalent / kwh) for single, plural, kwh in APPLIANCE_USES]
    readable = [item for item in counts if item[2] >= 1] or counts
    single, plural, count = min(readable, key=lambda item: abs(item[2] - 10))
    rounded = max(round(count), 1)
    return f"{rounded} {single if rounded == 1 else plural}"


def analogize(
    co2_reduction_lb: float,
    savings_usd: float,
    avg_intensity_lb_per_kwh: float,
    avg_rate_usd_per_kwh: float,
) -> list[str]:
    """Readable comparisons for the CO2 and dollars saved (negative = worse than naive)."""
    if avg_intensity_lb_per_kwh <= 0 or avg_rate_usd_per_kwh <= 0:
        return []

    lines = []
    co2 = abs(co2_reduction_lb)
    money = abs(savings_usd)

    if co2 > 0.01:
        verb = "avoids" if co2_reduction_lb >= 0 else "adds"
        pieces = []
        miles = co2 / CAR_LB_CO2_PER_MILE
        if miles >= 0.5:
            pieces.append(f"driving ~{miles:.1f} miles")
        pieces.append(f"running roughly {_most_readable(co2 / avg_intensity_lb_per_kwh)}")
        lines.append(f"Roughly speaking, this {verb} about as much CO2 as " + " or ".join(pieces) + " (approximate).")

    if money > 0.005:
        noun = "saving" if savings_usd >= 0 else "extra cost"
        lines.append(f"The {noun} is roughly what {_most_readable(money / avg_rate_usd_per_kwh)} costs to run (approximate).")
    return lines
