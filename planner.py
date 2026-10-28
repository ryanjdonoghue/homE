"""Planner page: reschedule a home asset, optimize it, and see the full impact."""

import pandas as pd
import streamlit as st

from analogies import analogize
from content import CHEAPEST_NUDGE, KW_VS_KWH, OPTIMIZE_HELP, SCALE_NOTE, SCHEDULE_WHY
from grid_data import FUEL_TYPE_NAMES
from home_changes import CHANGES
from impact import RATE_USD_PER_KWH, environmental_impact, financial_impact, hourly_carbon_intensity
from load_model import baseline_household
from narrate import narrate_change
from optimize import optimization_options
from ui_common import (
    apply_windows,
    cached_grid_mix,
    cached_hourly_grid_mix,
    format_hour_ampm,
    format_hour_range,
    format_windows,
    impact_metric,
    load_curve_chart,
)
from units import ENERGY_UNITS, POWER_UNITS, WORKED_EXAMPLE

st.title("Flipping the Switch")

st.subheader("Current U.S. grid mix")
grid_result = None
try:
    grid_result = cached_grid_mix()
    st.caption(f"Period: {grid_result['period']}")
    mix = grid_result["mix"]
    total = sum(mix.values())
    for fueltype, value in sorted(mix.items(), key=lambda item: item[1], reverse=True):
        name = FUEL_TYPE_NAMES.get(fueltype, fueltype)
        share = value / total if total else 0
        st.write(f"{name}: {value:,.0f} MWh ({share:.1%})")
except RuntimeError as exc:
    st.error(str(exc))

st.subheader("Shift a home asset's schedule")
change_names = [change.name for change in CHANGES]
selected_name = st.selectbox("Asset to reschedule", change_names)
selected_change = next(change for change in CHANGES if change.name == selected_name)
st.caption(selected_change.description)
st.caption(SCHEDULE_WHY)

baseline = baseline_household()
baseline_curve = baseline.hourly_load_kw()

carbon_curve = None
grid_error = None
try:
    carbon_curve = hourly_carbon_intensity(cached_hourly_grid_mix()["by_hour"])
except RuntimeError as exc:
    grid_error = str(exc)

options = []
if carbon_curve is not None:
    options = optimization_options(baseline, selected_change, carbon_curve)
    avg_intensity = sum(carbon_curve) / len(carbon_curve)
    avg_rate = sum(RATE_USD_PER_KWH) / len(RATE_USD_PER_KWH)

    st.markdown("**Don't want to try every option? Let the app find the best schedule.**")
    st.caption(OPTIMIZE_HELP)
    option_cols = st.columns(len(options))
    for column, option in zip(option_cols, options):
        with column:
            st.markdown(f"##### {option.goal}")
            st.caption(format_windows(selected_change, option.windows))
            impact_metric(st, "Daily cost saved", "Daily cost increase", option.money["savings_usd"], "$")
            impact_metric(st, "Daily CO2 avoided", "Daily CO2 increase", option.co2["co2_reduction_lb"], "lb")
            for line in analogize(option.co2["co2_reduction_lb"], option.money["savings_usd"], avg_intensity, avg_rate):
                st.caption(line)
            st.button(
                "Apply this schedule",
                key=f"apply-{selected_change.name}-{option.goal}",
                on_click=apply_windows,
                args=(selected_change, option.windows),
            )
else:
    st.info("Grid data isn't available, so the optimizer is disabled.")

st.markdown("**Or fine-tune it yourself**")
windows = []
for segment in selected_change.segments:
    st.markdown(f"**{segment.label}** — naive schedule: {format_hour_range(segment.naive_hours)}")
    seg_col1, seg_col2 = st.columns(2)
    start_key = f"{selected_change.name}-{segment.label}-start"
    duration_key = f"{selected_change.name}-{segment.label}-duration"
    # Keep the window inside the segment's period (morning stays before noon, evening after).
    start_options = segment.start_hours(1)
    if st.session_state.get(start_key, segment.default_start_hour) not in start_options:
        st.session_state[start_key] = segment.default_start_hour
    start_hour = seg_col1.select_slider(
        f"{segment.label}: new start time",
        options=start_options,
        value=segment.default_start_hour,
        format_func=format_hour_ampm,
        key=start_key,
    )
    max_duration = segment.max_duration(start_hour)
    if st.session_state.get(duration_key, segment.default_duration) > max_duration:
        st.session_state[duration_key] = max_duration
    if max_duration > 1:
        duration = seg_col2.slider(
            f"{segment.label}: new duration (hours)",
            min_value=1,
            max_value=max_duration,
            value=min(segment.default_duration, max_duration),
            key=duration_key,
        )
    else:
        duration = 1
        seg_col2.caption("Duration: 1 hour (the latest start leaves room for only one)")
    windows.append((start_hour, duration))

modified = selected_change.apply(baseline, windows)
modified_curve = modified.hourly_load_kw()

load_curve_chart(baseline_curve, modified_curve)

st.subheader("Financial & environmental impact")
money = None
co2 = None
analogy_lines = []
if carbon_curve is None:
    st.error(grid_error)
else:
    asset_baseline = selected_change.asset_curve(baseline)
    asset_modified = selected_change.asset_curve(modified)
    money = financial_impact(asset_baseline, asset_modified)
    co2 = environmental_impact(asset_baseline, asset_modified, carbon_curve)

    col1, col2 = st.columns(2)
    col1.metric(
        f"{selected_change.name} daily cost",
        f"${money['modified_cost_usd']:.2f}",
        f"{-money['savings_usd']:+.2f}",
        delta_color="inverse",
    )
    col2.metric(
        f"{selected_change.name} daily CO2",
        f"{co2['modified_co2_lb']:.2f} lb",
        f"{-co2['co2_reduction_lb']:+.2f} lb",
        delta_color="inverse",
    )
    st.caption(KW_VS_KWH)

    analogy_lines = analogize(co2["co2_reduction_lb"], money["savings_usd"], avg_intensity, avg_rate)
    for line in analogy_lines:
        st.write(line)

    # Counter-nudge: if the user chose the cheapest schedule, show what that gave up.
    by_goal = {option.goal: option for option in options}
    cheapest, cleanest = by_goal["Cheapest"], by_goal["Cleanest"]
    extra_co2 = cleanest.co2["co2_reduction_lb"] - co2["co2_reduction_lb"]
    if windows == cheapest.windows and cheapest.windows != cleanest.windows and extra_co2 > 0.01:
        extra_cost = money["savings_usd"] - cleanest.money["savings_usd"]
        st.warning(
            f"{CHEAPEST_NUDGE}\n\nThe cleanest schedule would avoid **{extra_co2:.1f} lb more CO2** per day "
            f"and cost **${extra_cost:.2f} more**. "
            + " ".join(analogize(extra_co2, 0.0, avg_intensity, avg_rate))
        )
    st.caption(SCALE_NOTE)

st.subheader("What this means")
if grid_result is None or money is None:
    st.info("Grid data isn't available, so narration is skipped.")
else:
    load_summary = {
        "financial_impact": money,
        "environmental_impact": co2,
    }
    try:
        narration = narrate_change(grid_result["mix"], load_summary, selected_change.description, analogy_lines)
        st.write(narration)
    except RuntimeError as exc:
        st.warning(f"Narration unavailable: {exc}")

with st.expander("Energy units cheat sheet (W, kW, MW, kWh...)"):
    st.markdown(WORKED_EXAMPLE)
    st.markdown("**Power** — how fast energy is being used")
    st.table(pd.DataFrame(POWER_UNITS).set_index("Unit"))
    st.markdown("**Energy** — how much was used over time")
    st.table(pd.DataFrame(ENERGY_UNITS).set_index("Unit"))

st.page_link("money_view.py", label="Experience the status quo for home energy management")
