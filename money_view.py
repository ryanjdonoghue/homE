"""Money view: the savings-only framing, with reveal-on-click commentary on what it hides."""

import streamlit as st

from analogies import analogize
from content import MONEY_COMMENTARY, MONEY_INTRO
from contrast import money_view_summary
from home_changes import CHANGES
from impact import hourly_carbon_intensity
from load_model import baseline_household
from ui_common import (
    cached_hourly_grid_mix,
    format_hour_ampm,
    format_windows,
    impact_metric,
    load_curve_chart,
)

REVEAL_ALL_KEY = "money-reveal-all"


def reveal_box(section: str) -> bool:
    """A 'What's missing?' toggle; returns True if the commentary should show."""
    own = st.toggle("**What's missing?**", key=f"money-reveal-{section}")
    return own or st.session_state.get(REVEAL_ALL_KEY, False)


st.title("The money view")
st.caption(MONEY_INTRO)
st.toggle("Reveal everything", key=REVEAL_ALL_KEY)
st.page_link("planner.py", label="Back to the full planner")

selected_name = st.selectbox("Asset to optimize", [change.name for change in CHANGES], key="money-asset")
change = next(c for c in CHANGES if c.name == selected_name)

try:
    carbon_curve = hourly_carbon_intensity(cached_hourly_grid_mix()["by_hour"])
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

summary = money_view_summary(baseline_household(), change, carbon_curve)

st.subheader("Your savings")
col1, col2, col3 = st.columns(3)
impact_metric(col1, "Saved per month", "Extra cost per month", summary["monthly_savings_usd"], "$")
impact_metric(col2, "Saved per year", "Extra cost per year", summary["annual_savings_usd"], "$")
col3.metric(
    f"{change.name} daily bill",
    f"${summary['cheapest_cost_usd']:.2f}",
    f"{-summary['daily_savings_usd']:+.2f}",
    delta_color="inverse",
)
st.caption(f"Best schedule for your bill: {format_windows(change, summary['windows'])}")
for line in analogize(0.0, summary["daily_savings_usd"], summary["avg_intensity"], summary["avg_rate"]):
    st.write(line)
if reveal_box("savings"):
    st.warning(MONEY_COMMENTARY["savings"].format(kwh=summary["baseline_kwh"]))

st.subheader("When you'd use power")
load_curve_chart(summary["baseline_curve"], summary["cheapest_curve"], "Cheapest schedule")
if reveal_box("chart"):
    before_hour, before_kw = summary["peak_before"]
    after_hour, after_kw = summary["peak_after"]
    if summary["intensity_after"] < summary["intensity_before"] - 0.005:
        verdict = "Here the cheaper hours happen to be cleaner too, but the bill would look the same either way."
    else:
        verdict = "Here the cheaper hours are no cleaner, and the bill would look just as good."
    if before_hour == after_hour:
        peak_sentence = (
            f"Your highest-load hour stays at **{format_hour_ampm(before_hour)}**, "
            f"changing from {before_kw:.1f} kW to {after_kw:.1f} kW."
        )
    else:
        peak_sentence = (
            f"Your highest-load hour moves from **{format_hour_ampm(before_hour)}** ({before_kw:.1f} kW) "
            f"to **{format_hour_ampm(after_hour)}** ({after_kw:.1f} kW)."
        )
    st.info(
        MONEY_COMMENTARY["chart"].format(
            before=summary["intensity_before"],
            after=summary["intensity_after"],
            verdict=verdict,
            peak_sentence=peak_sentence,
        )
    )

st.subheader("Bottom line")
st.success(f"Switch to this schedule and keep about **${summary['annual_savings_usd']:.0f} a year**.")
if reveal_box("co2"):
    co2_change = summary["co2_reduction_lb"]
    co2_phrase = (
        f"avoids {co2_change:.1f} lb of CO2 a day" if co2_change >= 0 else f"adds {-co2_change:.1f} lb of CO2 a day"
    )
    if summary["extra_co2_vs_cleanest_lb"] < 0.05:
        cleanest_sentence = "For this asset the cheapest and cleanest schedules are the same, so nothing is lost here."
    else:
        analogy = " ".join(
            analogize(summary["extra_co2_vs_cleanest_lb"], 0.0, summary["avg_intensity"], summary["avg_rate"])
        ).replace("This avoids CO2 equal to", "That's about the CO2 from")
        cleanest_sentence = (
            f"The cleanest schedule would do **{summary['extra_co2_vs_cleanest_lb']:.1f} lb/day better** on CO2 "
            f"and cost **${summary['extra_cost_of_cleanest_usd']:.2f}/day more**. {analogy}"
        )
    st.warning(
        MONEY_COMMENTARY["co2"].format(
            co2_phrase=co2_phrase,
            cleanest_sentence=cleanest_sentence,
        )
    )
if reveal_box("scale"):
    st.info(MONEY_COMMENTARY["scale"])

st.page_link("planner.py", label="Experience a shift away from monetary prioritization")