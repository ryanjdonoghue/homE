"""Short explanatory copy shown inline next to the planning controls and results."""

SCHEDULE_WHY = (
    "The naive hours are when people are home and everyone else is using power too. "
    "Demand peaks in the early evening, so electricity there is the most expensive "
    "and often comes from the dirtiest plants running to keep up."
)

OPTIMIZE_HELP = (
    "Optimize checks every possible start time for each routine, keeping its run length the same, "
    "and scores each one on this app's rate plan and yesterday's grid mix. "
    "**Cheapest** minimizes your bill, **Cleanest** minimizes CO2, and **Balanced** weighs both equally. "
    "They don't always agree: the cheapest hours aren't always the cleanest."
)

CHEAPEST_NUDGE = (
    "You picked the cheapest schedule. Dollars are only one measure of conservation: "
    "the rate plan here is an assumption, and a cheaper hour isn't necessarily a cleaner one."
)

SCALE_NOTE = (
    "Shifting a few kWh doesn't change how much energy you use, only when. The bigger "
    "levers for the climate are how much energy a whole society consumes and how it is generated."
)

KW_VS_KWH = "Power (kW) is how fast you use energy; energy (kWh) is how much you use. See the units cheat sheet below."

# Commentary boxes on the money-view page; each names what the money framing leaves out.
MONEY_INTRO = (
    "This is the view most energy tools give you: one number, how much less you pay. "
    "Look at it as a typical consumer would, then click **What's missing?** to see what it leaves out."
)

MONEY_COMMENTARY = {
    "savings": (
        "**This is a bill number, not an energy number.** You use **{kwh:.1f} kWh** a day on the naive schedule "
        "and **{kwh:.1f} kWh** on this one: the same energy, just at a cheaper time. The savings also depend on "
        "an assumed time-of-use rate plan (the app's illustrative one), and the yearly figure simply assumes every "
        "day looks like today."
    ),
    "chart": (
        "**A price signal doesn't tell you what the grid is burning.** The electricity behind your load averaged "
        "**{before:.2f} lb CO2/kWh** on the naive schedule and **{after:.2f} lb CO2/kWh** on this one. {verdict} "
        "{peak_sentence}"
    ),
    "co2": (
        "**Emissions weren't part of the question.** This schedule {co2_phrase}. {cleanest_sentence}"
    ),
    "scale": (
        "**Savings land on one bill; the grid stays the same.** Your household keeps the savings, but shared "
        "infrastructure, the fuel mix and total demand don't change when load only moves around. A money signal "
        "is only as good as the rate plan behind it, so chasing the lowest bill can reward habits that don't "
        "help the grid or the climate. Conservation also means using less and using cleaner power, not only paying less."
    ),
}
