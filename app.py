"""Streamlit entrypoint for Flipping the Switch."""

import altair as alt
import pandas as pd
import streamlit as st

from grid_data import FUEL_TYPE_NAMES, get_grid_mix, get_hourly_grid_mix
from home_changes import CHANGES
from impact import environmental_impact, financial_impact, hourly_carbon_intensity
from load_model import baseline_household
from narrate import narrate_change

STATUS_CRITICAL = "#d03b3b"  # naive schedule: the problem being fixed
STATUS_GOOD = "#0ca30c"  # your schedule: the chosen fix


def format_hour_ampm(hour: int) -> str:
    period = "AM" if hour < 12 else "PM"
    display_hour = hour % 12 or 12
    return f"{display_hour} {period}"


def format_hour_range(hours: list[int]) -> str:
    hours = sorted(hours)
    if len(hours) == 1:
        return format_hour_ampm(hours[0])
    return f"{format_hour_ampm(hours[0])}–{format_hour_ampm(hours[-1])}"


st.title("Flipping the Switch")

st.subheader("Current U.S. grid mix")
grid_result = None
try:
    grid_result = get_grid_mix()
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

windows = []
for segment in selected_change.segments:
    st.markdown(f"**{segment.label}** — naive schedule: {format_hour_range(segment.naive_hours)}")
    seg_col1, seg_col2 = st.columns(2)
    start_hour = seg_col1.select_slider(
        f"{segment.label}: new start time",
        options=list(range(24)),
        value=segment.default_start_hour,
        format_func=format_hour_ampm,
        key=f"{selected_change.name}-{segment.label}-start",
    )
    duration = seg_col2.slider(
        f"{segment.label}: new duration (hours)",
        min_value=1,
        max_value=12,
        value=segment.default_duration,
        key=f"{selected_change.name}-{segment.label}-duration",
    )
    windows.append((start_hour, duration))

baseline = baseline_household()
modified = selected_change.apply(baseline, windows)
baseline_curve = baseline.hourly_load_kw()
modified_curve = modified.hourly_load_kw()

chart_data = pd.DataFrame(
    {
        "hour": list(range(24)) * 2,
        "kw": baseline_curve + modified_curve,
        "schedule": ["Naive schedule"] * 24 + ["Your schedule"] * 24,
    }
)
chart = (
    alt.Chart(chart_data)
    .mark_line(strokeWidth=2)
    .encode(
        x=alt.X(
            "hour:Q",
            title="Time of day",
            axis=alt.Axis(values=[0, 3, 6, 9, 12, 15, 18, 21], labelExpr=(
                "datum.value == 0 ? '12 AM' : datum.value < 12 ? datum.value + ' AM' : "
                "datum.value == 12 ? '12 PM' : (datum.value - 12) + ' PM'"
            )),
        ),
        y=alt.Y("kw:Q", title="Household load (kW)"),
        color=alt.Color(
            "schedule:N",
            title="Schedule",
            scale=alt.Scale(domain=["Naive schedule", "Your schedule"], range=[STATUS_CRITICAL, STATUS_GOOD]),
        ),
        tooltip=[alt.Tooltip("schedule:N"), alt.Tooltip("hour:Q", title="Hour"), alt.Tooltip("kw:Q", title="kW", format=".2f")],
    )
)
st.altair_chart(chart, use_container_width=True)

st.subheader("Financial & environmental impact")
money = None
co2 = None
try:
    hourly_mix = get_hourly_grid_mix()
    carbon_curve = hourly_carbon_intensity(hourly_mix["by_hour"])

    money = financial_impact(baseline_curve, modified_curve)
    co2 = environmental_impact(baseline_curve, modified_curve, carbon_curve)

    col1, col2 = st.columns(2)
    col1.metric(
        "Daily cost",
        f"${money['modified_cost_usd']:.2f}",
        f"{-money['savings_usd']:+.2f}",
        delta_color="inverse",
    )
    col2.metric(
        "Daily CO2",
        f"{co2['modified_co2_lb']:.1f} lb",
        f"{-co2['co2_reduction_lb']:+.1f} lb",
        delta_color="inverse",
    )
except RuntimeError as exc:
    st.error(str(exc))

st.subheader("What this means")
if grid_result is None or money is None:
    st.info("Grid data isn't available, so narration is skipped.")
else:
    load_summary = {
        "financial_impact": money,
        "environmental_impact": co2,
    }
    try:
        narration = narrate_change(grid_result["mix"], load_summary, selected_change.description)
        st.write(narration)
    except RuntimeError as exc:
        st.warning(f"Narration unavailable: {exc}")
