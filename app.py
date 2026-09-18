"""Streamlit entrypoint for Flipping the Switch."""

import streamlit as st

from grid_data import FUEL_TYPE_NAMES, get_grid_mix

st.title("Flipping the Switch")

st.subheader("Current U.S. grid mix")
try:
    result = get_grid_mix()
    st.caption(f"Period: {result['period']}")
    mix = result["mix"]
    total = sum(mix.values())
    for fueltype, value in sorted(mix.items(), key=lambda item: item[1], reverse=True):
        name = FUEL_TYPE_NAMES.get(fueltype, fueltype)
        share = value / total if total else 0
        st.write(f"{name}: {value:,.0f} MWh ({share:.1%})")
except RuntimeError as exc:
    st.error(str(exc))
