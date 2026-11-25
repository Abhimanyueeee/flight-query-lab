"""Row validation: airport list loading, single-row checks, record building."""
import math
import re
from datetime import datetime

# ASCII only on purpose - str.isalnum()/isupper() would let in non-ASCII letters
FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}")
AIRPORT_RE = re.compile(r"[A-Z]{3}")
# strptime alone accepts "2025-1-5 9:3", so the shape is checked first
DATETIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def parse_datetime(text: str) -> datetime | None:
    """Return a datetime if text is exactly 'YYYY-MM-DD HH:MM' and real, else None."""
    if not DATETIME_RE.fullmatch(text):
        return None
    try:
        return datetime.strptime(text, DATETIME_FORMAT)
    except ValueError:
        return None


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes.

    One code per line. Strip whitespace; skip blank lines and lines
    starting with '#'.
    """
    codes = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            codes.add(line)
    return codes


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """
    # 1
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    flight_id, origin, destination, departure, arrival, price = (f.strip() for f in fields)

    # 2
    if not all((flight_id, origin, destination, departure, arrival, price)):
        return "MISSING_FIELD"

    # 3
    if not FLIGHT_ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"

    # 4, 5
    if not AIRPORT_RE.fullmatch(origin) or origin not in airports:
        return "INVALID_ORIGIN"
    if not AIRPORT_RE.fullmatch(destination) or destination not in airports:
        return "INVALID_DESTINATION"

    # 6
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    # 7, 8
    dep = parse_datetime(departure)
    if dep is None:
        return "INVALID_DEPARTURE"
    arr = parse_datetime(arrival)
    if arr is None:
        return "INVALID_ARRIVAL"

    # 9
    if arr <= dep:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    # 10, 11
    try:
        value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(value):
        return "INVALID_PRICE"
    if value <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """
    flight_id, origin, destination, departure, arrival, price = (f.strip() for f in fields)
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": departure,
        "arrival_datetime": arrival,
        "price": float(price),
    }