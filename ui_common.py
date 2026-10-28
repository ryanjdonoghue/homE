"""Helpers shared by the planner and money-view pages."""

import altair as alt
import pandas as pd
import streamlit as st

from grid_data import get_grid_mix, get_hourly_grid_mix

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


def impact_metric(column, good_label: str, bad_label: str, value: float, unit: str) -> None:
    """Metric whose label flips (e.g. saved -> increase) and whose arrow points the way the quantity moves
    (up = increase, down = decrease), red for an increase and green for a decrease."""
    amount = f"${abs(value):.2f}" if unit == "$" else f"{abs(value):.2f} {unit}"
    delta = f"{'-' if value >= 0 else '+'}{amount}"
    column.metric(good_label if value >= 0 else bad_label, amount, delta, delta_color="inverse")


def format_windows(change, windows: list[tuple[int, int]]) -> str:
    parts = []
    for segment, (start, duration) in zip(change.segments, windows):
        end = (start + duration) % 24
        parts.append(f"{segment.label}: {format_hour_ampm(start)}–{format_hour_ampm(end)}")
    return " · ".join(parts)


def apply_windows(change, windows: list[tuple[int, int]]) -> None:
    """Button callback: push an optimizer result into the schedule sliders."""
    for segment, (start, duration) in zip(change.segments, windows):
        st.session_state[f"{change.name}-{segment.label}-start"] = start
        st.session_state[f"{change.name}-{segment.label}-duration"] = duration


# Grid data is re-fetched from EIA on every call; cache so slider moves don't re-hit the API.
cached_grid_mix = st.cache_data(ttl=600)(get_grid_mix)
cached_hourly_grid_mix = st.cache_data(ttl=600)(get_hourly_grid_mix)


def load_curve_chart(baseline_curve: list[float], modified_curve: list[float], modified_label: str = "Your schedule") -> None:
    """Line chart of household kW by hour: naive schedule vs a modified one."""
    chart_data = pd.DataFrame(
        {
            "hour": list(range(24)) * 2,
            "kw": baseline_curve + modified_curve,
            "schedule": ["Naive schedule"] * 24 + [modified_label] * 24,
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
                scale=alt.Scale(domain=["Naive schedule", modified_label], range=[STATUS_CRITICAL, STATUS_GOOD]),
            ),
            tooltip=[alt.Tooltip("schedule:N"), alt.Tooltip("hour:Q", title="Hour"), alt.Tooltip("kw:Q", title="kW", format=".2f")],
        )
    )
    st.altair_chart(chart, width="stretch")
