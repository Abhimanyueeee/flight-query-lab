"""Row validation: airport list loading, single-row checks, record building."""
import math
import re
from datetime import datetime

# Regular expressions. We always use fullmatch(), so the WHOLE text must match.
# We write [A-Za-z0-9] and [0-9] on purpose: isalnum() and \d also accept
# non-ASCII characters (like "A-macron" or Arabic digits), and we must reject them.
FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}")  # 2-8 ASCII letters or digits
AIRPORT_RE = re.compile(r"[A-Z]{3}")  # exactly 3 uppercase ASCII letters
# Exact shape of a datetime: zero-padded, one space, 24-hour clock.
# This rejects things like "2025-1-5 9:3" that strptime would accept.
DATETIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def parse_datetime(text: str) -> datetime | None:
    """Return a datetime if text is exactly 'YYYY-MM-DD HH:MM' and real, else None."""
    # Step 1: check the shape of the text (the format must be exact).
    if not DATETIME_RE.fullmatch(text):
        return None
    # Step 2: check that the date and time really exist
    # (for example, month 13 or 30 February fail here).
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
            # Skip empty lines and comment lines.
            if not line or line.startswith("#"):
                continue
            # Keep the code exactly as written (comparison is case-sensitive).
            codes.add(line)
    return codes


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """
    # Check 1: the row must have exactly 6 fields.
    # (This must come before unpacking, or Python would raise an error.)
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    # Remove spaces around every field, then give each field a name.
    flight_id, origin, destination, departure, arrival, price = (f.strip() for f in fields)

    # Check 2: no field may be empty (an empty string counts as False).
    if not all((flight_id, origin, destination, departure, arrival, price)):
        return "MISSING_FIELD"

    # Check 3: flight id must be 2-8 ASCII letters or digits.
    if not FLIGHT_ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"

    # Checks 4 and 5: code must have the right shape AND be in the airport list.
    if not AIRPORT_RE.fullmatch(origin) or origin not in airports:
        return "INVALID_ORIGIN"
    if not AIRPORT_RE.fullmatch(destination) or destination not in airports:
        return "INVALID_DESTINATION"

    # Check 6: a flight cannot start and end at the same airport.
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    # Checks 7 and 8: both datetimes must be valid.
    # We keep the parsed values (dep, arr) to compare them in the next check.
    dep = parse_datetime(departure)
    if dep is None:
        return "INVALID_DEPARTURE"
    arr = parse_datetime(arrival)
    if arr is None:
        return "INVALID_ARRIVAL"

    # Check 9: arrival must be strictly later than departure.
    if arr <= dep:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    # Check 10: price must be a number that float() accepts...
    try:
        value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    # ...and it must be a normal number (nan, inf and -inf are not allowed).
    if not math.isfinite(value):
        return "INVALID_PRICE"
    # Check 11: price must be greater than zero.
    if value <= 0:
        return "NON_POSITIVE_PRICE"

    # All checks passed: the row is valid.
    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """
    # Only call this on rows that already passed validate_row().
    flight_id, origin, destination, departure, arrival, price = (f.strip() for f in fields)
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": departure,
        "arrival_datetime": arrival,
        # The price is the only value that is stored as a number, not text.
        "price": float(price),
    }