"""EIA grid-mix data fetching."""

import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

EIA_API_KEY = os.environ.get("EIA_API_KEY")
BASE_URL = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"
CACHE_PATH = Path(__file__).parent / "grid_mix_cache.json"

FUEL_TYPE_NAMES = {
    "COL": "Coal",
    "NG": "Natural Gas",
    "NUC": "Nuclear",
    "OIL": "Petroleum",
    "WAT": "Hydro",
    "SUN": "Solar",
    "WND": "Wind",
    "GEO": "Geothermal",
    "BAT": "Battery Storage",
    "PS": "Pumped Storage",
    "OTH": "Other",
    "UNK": "Unknown",
}


def fetch_latest_fuel_mix(respondent="US48"):
    """Fetch the most recent hourly generation (MWh) by fuel type for a respondent."""
    if not EIA_API_KEY:
        raise RuntimeError("EIA_API_KEY is not set. Add it to your .env file.")

    params = {
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": respondent,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": 5000,
        "api_key": EIA_API_KEY,
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    rows = response.json()["response"]["data"]

    latest_period = rows[0]["period"]
    mix = {
        row["fueltype"]: float(row["value"])
        for row in rows
        if row["period"] == latest_period and row["value"] not in (None, "")
    }

    result = {"period": latest_period, "mix": mix}
    _write_cache(respondent, result)
    return result


def get_grid_mix(respondent="US48"):
    """Get the current grid fuel mix, falling back to the local cache if the API call fails."""
    try:
        return fetch_latest_fuel_mix(respondent)
    except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
        cached = _read_cache(respondent)
        if cached is None:
            raise RuntimeError(
                f"EIA API request failed and no cached data is available for {respondent}"
            ) from exc
        return cached


def _write_cache(respondent, result):
    cache = _read_all_cache()
    cache[respondent] = {**result, "cached_at": time.time()}
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def _read_cache(respondent):
    return _read_all_cache().get(respondent)


def _read_all_cache():
    if not CACHE_PATH.exists():
        return {}
    return json.loads(CACHE_PATH.read_text())
