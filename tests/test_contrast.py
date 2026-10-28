import pytest

from contrast import DAYS_PER_YEAR, money_view_summary
from home_changes import CHANGES
from load_model import baseline_household
from test_optimize import CARBON_CURVE


@pytest.mark.parametrize("change", CHANGES, ids=lambda c: c.name)
def test_money_view_hides_unchanged_energy_and_extra_co2(change):
    summary = money_view_summary(baseline_household(), change, CARBON_CURVE)
    assert summary["cheapest_kwh"] == pytest.approx(summary["baseline_kwh"])
    assert summary["annual_savings_usd"] == pytest.approx(summary["daily_savings_usd"] * DAYS_PER_YEAR)
    assert summary["extra_co2_vs_cleanest_lb"] >= -1e-9
    assert summary["extra_cost_of_cleanest_usd"] >= -1e-9


def test_daily_bill_covers_only_the_selected_asset():
    house = baseline_household()
    lighting = next(c for c in CHANGES if c.name == "Lighting")
    summary = money_view_summary(house, lighting, CARBON_CURVE)
    assert summary["baseline_kwh"] == pytest.approx(sum(lighting.asset_curve(house)))
    assert summary["baseline_cost_usd"] < 3
    assert summary["baseline_cost_usd"] - summary["cheapest_cost_usd"] == pytest.approx(summary["daily_savings_usd"])
