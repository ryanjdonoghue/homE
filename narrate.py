"""Sonnet 5 calls for interpreting results."""

import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "You are an energy analyst explaining household electricity changes to a "
    "homeowner. Given the current grid fuel mix and the effect of a home change "
    "on household load, write a short, concrete explanation of what the change "
    "means in practice. Stick to what the data supports; do not speculate beyond it."
)

_client = None


def _get_client():
    global _client
    if _client is None:
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
            raise RuntimeError(
                "No Anthropic credentials found. Set ANTHROPIC_API_KEY, or "
                "ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN for a gateway (e.g. Portkey), in your .env file."
            )
        # No explicit api_key/base_url: the SDK resolves ANTHROPIC_API_KEY, then
        # ANTHROPIC_AUTH_TOKEN, and reads ANTHROPIC_BASE_URL itself.
        _client = Anthropic()
    return _client


def narrate_change(grid_mix: dict, load_summary: dict, change_description: str) -> str:
    """Interpret a home change against the current grid mix and household load.

    Returns the narrative text, or raises RuntimeError if the request fails.
    """
    client = _get_client()
    user_prompt = (
        f"Current grid fuel mix (MWh by source): {grid_mix}\n"
        f"Household load impact: {load_summary}\n"
        f"Change being evaluated: {change_description}\n\n"
        "Explain what this change means for the household's energy use and its "
        "connection to the current grid mix, in 2-4 sentences."
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:
        raise RuntimeError(f"Sonnet request failed: {type(exc).__name__}") from exc

    return response.content[0].text
