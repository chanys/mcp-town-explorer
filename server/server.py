"""MCP server for the town explorer.

FastMCP + stdio transport. Exposes three narrow tools and one resource over
JSON-RPC. The two hosts (v1_cli, v2_llm) talk to this exact server unchanged.
"""

import csv
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "towns.csv"

# Column -> converter. This doubles as a schema check on read: a missing column
# or an uncoercible cell raises loudly here at startup, so bad data cannot flow
# silently into a tool result. This is the one place we validate the data boundary.
_FIELDS = {
    "town": str,
    "median_home_price": int,
    "violent_crime_rate": float,
    "school_rating": int,
    "distance_to_boston_mi": float,
    "population": int,
}


def _load(path: Path) -> dict[str, dict]:
    """Read the CSV once into a dict keyed by lowercased town name."""
    towns: dict[str, dict] = {}
    with path.open(newline="") as f:
        for line in csv.DictReader(f):
            row = {col: conv(line[col]) for col, conv in _FIELDS.items()}
            towns[row["town"].lower()] = row
    if not towns:
        raise ValueError(f"No rows loaded from {path}")
    return towns


TOWNS = _load(DATA_PATH)

mcp = FastMCP("town-explorer")


def _lookup(town: str) -> dict:
    """Find a town or raise, so the error surfaces across the protocol."""
    row = TOWNS.get(town.lower())
    if row is None:
        known = ", ".join(sorted(r["town"] for r in TOWNS.values()))
        raise ValueError(f"Unknown town: {town!r}. Known towns: {known}")
    return row


@mcp.tool()
def get_housing(town: str) -> dict:
    """Median home price for one town, in USD."""
    row = _lookup(town)
    return {"town": row["town"], "median_home_price": row["median_home_price"]}


@mcp.tool()
def get_distance(town: str) -> dict:
    """Straight-line distance from one town to Boston, in miles."""
    row = _lookup(town)
    return {"town": row["town"], "distance_to_boston_mi": row["distance_to_boston_mi"]}


@mcp.tool()
def get_schools(town: str) -> dict:
    """School rating for one town (GreatSchools district rating, 1-10)."""
    row = _lookup(town)
    return {"town": row["town"], "school_rating": row["school_rating"]}


@mcp.tool()
def get_safety(town: str) -> dict:
    """Crime figures for one town: violent crime rate as incidents per 1,000 residents."""
    row = _lookup(town)
    return {"town": row["town"], "violent_crime_rate": row["violent_crime_rate"]}


@mcp.resource("town://{town}")
def town_profile(town: str) -> str:
    """Human-readable full profile for one town."""
    r = _lookup(town)
    return (
        f"{r['town']}, MA\n"
        f"  Median home price: ${r['median_home_price']:,}\n"
        f"  School rating (GreatSchools): {r['school_rating']}/10\n"
        f"  Violent crime rate: {r['violent_crime_rate']} per 1,000\n"
        f"  Distance to Boston: {r['distance_to_boston_mi']} mi\n"
        f"  Population: {r['population']:,}\n"
    )


if __name__ == "__main__":
    # stdio transport: the host launches this file as a subprocess and speaks
    # JSON-RPC over stdin/stdout. No network, no port.
    mcp.run()
