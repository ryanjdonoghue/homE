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


def _fetch_rows(respondent, length):
    if not EIA_API_KEY:
        raise RuntimeError("EIA_API_KEY is not set. Add it to your .env file.")

    params = {
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": respondent,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": length,
        "api_key": EIA_API_KEY,
    }
    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()["response"]["data"]


def fetch_latest_fuel_mix(respondent="US48"):
    """Fetch the most recent hourly generation (MWh) by fuel type for a respondent."""
    rows = _fetch_rows(respondent, length=len(FUEL_TYPE_NAMES) * 3)

    latest_period = rows[0]["period"]
    mix = {
        row["fueltype"]: float(row["value"])
        for row in rows
        if row["period"] == latest_period and row["value"] not in (None, "")
    }

    result = {"period": latest_period, "mix": mix}
    _write_cache("latest", respondent, result)
    return result


def get_grid_mix(respondent="US48"):
    """Get the current grid fuel mix, falling back to the local cache if the API call fails."""
    try:
        return fetch_latest_fuel_mix(respondent)
    except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
        cached = _read_cache("latest", respondent)
        if cached is None:
            raise RuntimeError(
                f"EIA API request failed and no cached data is available for {respondent}"
            ) from exc
        return cached


def fetch_recent_fuel_mix_by_hour(respondent="US48", num_periods=24):
    """Fetch fuel mix for each of the last `num_periods` hourly periods,
    keyed by hour-of-day (0-23), reflecting the most recent day observed.
    """
    rows = _fetch_rows(respondent, length=num_periods * (len(FUEL_TYPE_NAMES) + 4))

    by_period = {}
    for row in rows:
        if row["value"] in (None, ""):
            continue
        by_period.setdefault(row["period"], {})[row["fueltype"]] = float(row["value"])

    recent_periods = sorted(by_period, reverse=True)[:num_periods]
    by_hour = {int(period[-2:]): by_period[period] for period in recent_periods}

    result = {"by_hour": by_hour}
    _write_cache("hourly", respondent, result)
    return result


def get_hourly_grid_mix(respondent="US48", num_periods=24):
    """Get the last day's fuel mix by hour-of-day, falling back to the local cache."""
    try:
        return fetch_recent_fuel_mix_by_hour(respondent, num_periods)
    except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
        cached = _read_cache("hourly", respondent)
        if cached is None:
            raise RuntimeError(
                f"EIA API request failed and no cached hourly data is available for {respondent}"
            ) from exc
        return cached


def _write_cache(kind, respondent, result):
    cache = _read_all_cache()
    cache.setdefault(kind, {})[respondent] = {**result, "cached_at": time.time()}
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def _read_cache(kind, respondent):
    return _read_all_cache().get(kind, {}).get(respondent)


def _read_all_cache():
    if not CACHE_PATH.exists():
        return {}
    return json.loads(CACHE_PATH.read_text())
