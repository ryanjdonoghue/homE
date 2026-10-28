# Flipping the Switch (homE)

A Streamlit app that shows how *when* a household uses electricity changes its cost and its carbon emissions. Pick a home asset (EV charger, water heater, lighting), shift its schedule by hand or let the app optimize it, and see the dollar and CO2 impact next to the current U.S. grid mix.

The app has two pages:

- **Plan your home** (default): grid mix, schedule controls, an **Optimize for me** button (Cheapest / Balanced / Cleanest), a naive-vs-yours load chart, cost and CO2 impact with everyday analogies, an energy-units cheat sheet, and an AI-written explanation.
- **The money view**: the savings-only framing most energy tools use, with **What's missing?** toggles that reveal what a money-only view leaves out (unchanged kWh, CO2, grid carbon intensity, the assumed rate plan).

## Setup

Requires Python 3.10+.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
EIA_API_KEY=your_eia_key                 # required, free at https://www.eia.gov/opendata/
ANTHROPIC_API_KEY=your_anthropic_key     # needed for the AI explanation
```

For an Anthropic gateway, set `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` instead of `ANTHROPIC_API_KEY`. Without Anthropic credentials the app still runs; the explanation shows a warning.

## Run

```bash
python3 -m streamlit run app.py
```

## Tests

```bash
python3 -m pytest
```

## How it works

| File | Role |
| --- | --- |
| `app.py` | Router between the two pages |
| `planner.py`, `money_view.py` | The two pages |
| `ui_common.py` | Shared UI helpers and cached grid fetches |
| `grid_data.py` | Pulls hourly fuel mix from the EIA API; falls back to `grid_mix_cache.json` if the API fails |
| `load_model.py` | Household "digital twin": appliances and their hourly kW |
| `home_changes.py` | Reschedulable assets and their routines; moves energy to a chosen window |
| `impact.py` | Daily cost (time-of-use rate) and CO2 (grid carbon intensity by hour) |
| `optimize.py` | Tries every start hour for each routine and picks the best by cost, CO2, or both |
| `contrast.py` | Numbers behind the money view's commentary |
| `analogies.py`, `units.py`, `content.py` | Everyday comparisons, the units cheat sheet, and explanatory copy |
| `narrate.py` | Claude-written explanation of the result |

**Optimizer:** for each routine, it keeps the run length the same and tries all 24 start hours, scoring each on the app's own rate table and hourly carbon curve. Cheapest minimizes cost, Cleanest minimizes CO2, and Balanced weighs both relative to the naive schedule.

## Limitations

- Electricity rates and per-fuel emissions factors are **illustrative**, not tied to a real utility or measured data.
- The carbon signal is the **average** grid mix from the last 24 hours of EIA data (yesterday's pattern), not a forecast and not marginal emissions.
- Rescheduling **moves** energy use; it doesn't reduce total kWh. Savings are in cost and CO2.
- The money view's monthly and yearly figures just multiply one day by 30 or 365.
- The household has four appliances and doesn't model a full home.

## Troubleshooting

- *"Grid data isn't available"*: check `EIA_API_KEY`. If the API is down, a previously cached `grid_mix_cache.json` is used.
- If `streamlit` or `pytest` fail with "bad interpreter" after moving the project folder, recreate the venv or use the `python -m ...` forms above.
