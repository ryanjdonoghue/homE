"""Energy and power units with scale examples, for the in-app cheat sheet.

Examples are approximate and meant to give a feel for scale.
"""

# Power: how fast energy is used right now.
POWER_UNITS = [
    {"Unit": "W (watt)", "Equals": "1 W", "Example": "A phone charger is about 5-10 W; an LED bulb about 10 W."},
    {"Unit": "kW (kilowatt)", "Equals": "1,000 W", "Example": "Household scale: a microwave is ~1.1 kW, a space heater ~1.5 kW, this app's EV charger 1.4 kW."},
    {"Unit": "MW (megawatt)", "Equals": "1,000 kW", "Example": "Utility scale: a large solar field makes about 1-100+ MW; 1 MW can serve roughly 150-200 homes."},
    {"Unit": "GW (gigawatt)", "Equals": "1,000 MW", "Example": "Power-plant scale: one nuclear reactor is about 1 GW, enough for several hundred thousand homes."},
]

# Energy: power used over time.
ENERGY_UNITS = [
    {"Unit": "Wh (watt-hour)", "Equals": "1 W for 1 hour", "Example": "An LED bulb running for 6 minutes."},
    {"Unit": "kWh (kilowatt-hour)", "Equals": "1,000 Wh", "Example": "What your bill counts. A typical home uses about 30 kWh a day; a washing machine cycle is ~0.5 kWh."},
    {"Unit": "MWh (megawatt-hour)", "Equals": "1,000 kWh", "Example": "About a month of electricity for one home; the grid mix above is shown in MWh per hour."},
    {"Unit": "GWh (gigawatt-hour)", "Equals": "1,000 MWh", "Example": "City scale: roughly a day of electricity for a town of tens of thousands of homes."},
    {"Unit": "TWh (terawatt-hour)", "Equals": "1,000 GWh", "Example": "Country scale: the U.S. uses roughly 4,000 TWh of electricity a year (approximate)."},
]

WORKED_EXAMPLE = (
    "**Power x time = energy.** This app's EV charger draws 1.4 kW. "
    "Run for 4 hours, that's 1.4 kW x 4 h = 5.6 kWh, which is the number your bill counts. "
    "Moving the charge to a different hour changes *when* those 5.6 kWh are used, not how many."
)
