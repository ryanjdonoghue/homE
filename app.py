"""Streamlit entrypoint for Flipping the Switch: routes between the two pages."""

import streamlit as st

st.set_page_config(page_title="Flipping the Switch")

pages = st.navigation(
    [
        st.Page("planner.py", title="Plan your home", default=True),
        st.Page("money_view.py", title="The money view"),
    ]
)
pages.run()
