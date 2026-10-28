import pytest

from analogies import analogize
from home_changes import CHANGES
from load_model import baseline_household
from optimize import optimization_options

# Dirtiest in the evening, cleanest mid-day, so cheapest and cleanest differ.
CARBON_CURVE = [0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.4,
                0.4, 0.4, 0.5, 0.6, 0.8, 1.0, 1.2, 1.2, 1.1, 1.0, 0.95, 0.9]


@pytest.mark.parametrize("change", CHANGES, ids=lambda c: c.name)
def test_options_conserve_energy_and_order_goals(change):
    house = baseline_household()
    base_total = sum(house.hourly_load_kw())
    options = {o.goal: o for o in optimization_options(house, change, CARBON_CURVE)}
    for option in options.values():
        modified = change.apply(house, option.windows)
        assert sum(modified.hourly_load_kw()) == pytest.approx(base_total)
    assert options["Cheapest"].money["savings_usd"] >= options["Cleanest"].money["savings_usd"] - 1e-9
    assert options["Cleanest"].co2["co2_reduction_lb"] >= options["Cheapest"].co2["co2_reduction_lb"] - 1e-9


def test_overlapping_segments_do_not_destroy_energy():
    change = next(c for c in CHANGES if c.name == "Lighting")
    house = baseline_household()
    base_total = sum(house.hourly_load_kw())
    # Morning routine moved onto the evening routine's naive hours.
    modified = change.apply(house, [(18, 2), (17, 5)])
    assert sum(modified.hourly_load_kw()) == pytest.approx(base_total)


def test_analogies_never_say_zero():
    for co2, usd in [(0.3, 0.05), (5.0, 2.0), (-2.0, -0.4), (40.0, 8.0)]:
        for line in analogize(co2, usd, 0.9, 0.2):
            assert " 0 " not in line


@pytest.mark.parametrize("change", CHANGES, ids=lambda c: c.name)
def test_optimized_windows_stay_in_their_period(change):
    for option in optimization_options(baseline_household(), change, CARBON_CURVE):
        for segment, (start, duration) in zip(change.segments, option.windows):
            if segment.period:
                lo, hi = segment.period
                assert lo <= start and start + duration <= hi


def test_asset_daily_costs_are_realistic():
    from impact import RATE_USD_PER_KWH

    costs = {
        c.name: sum(k * r for k, r in zip(c.asset_curve(baseline_household()), RATE_USD_PER_KWH)) for c in CHANGES
    }
    assert 1.5 <= costs["EV charging"] <= 2.5
    assert 1.5 <= costs["Water heater"] <= 2.5  # about $45-75 a month
    assert costs["Lighting"] <= 2.1
