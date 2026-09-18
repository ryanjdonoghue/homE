"""Streamlit entrypoint for Flipping the Switch."""

import streamlit as st

from grid_data import FUEL_TYPE_NAMES, get_grid_mix
from home_changes import CHANGES
from load_model import baseline_household
from narrate import narrate_change

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
selected_name = st.selectbox("Change to apply", change_names)
selected_change = next(change for change in CHANGES if change.name == selected_name)
st.caption(selected_change.description)

baseline = baseline_household()
modified = selected_change.apply(baseline)
baseline_curve = baseline.hourly_load_kw()
modified_curve = modified.hourly_load_kw()

st.line_chart({"Baseline": baseline_curve, "After change": modified_curve})

st.subheader("What this means")
if grid_result is None:
    st.info("Grid data isn't available, so narration is skipped.")
else:
    load_summary = {
        "baseline_hourly_kw": baseline_curve,
        "modified_hourly_kw": modified_curve,
    }
    try:
        narration = narrate_change(grid_result["mix"], load_summary, selected_change.description)
        st.write(narration)
    except RuntimeError as exc:
        st.warning(f"Narration unavailable: {exc}")
