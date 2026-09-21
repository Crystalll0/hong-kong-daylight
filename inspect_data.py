# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check dates and times before plotting the saved HKO file."""
import csv
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data" / "hko-sunrise-sunset-2026.csv"


def to_minutes(clock):
    """Convert HH:MM text to minutes since midnight."""
    hour, minute = map(int, clock.split(":"))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Invalid time: {clock}")
    return hour * 60 + minute


def main():
    with DATA.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected = [date(2026, 1, 1) + timedelta(days=i) for i in range(365)]
    actual = [date.fromisoformat(row["YYYY-MM-DD"]) for row in rows]
    if actual != expected:
        raise ValueError("Dates must cover 2026 in order, without gaps or duplicates")
    lengths = []
    for row in rows:
        sunrise = to_minutes(row["RISE"])
        sunset = to_minutes(row["SET"])
        transit = to_minutes(row["TRAN."])
        if not sunrise < transit < sunset:
            raise ValueError(f"Unexpected times: {row}")
        lengths.append(sunset - sunrise)
    print(f"Validated {len(rows)} daily records: {actual[0]} to {actual[-1]}")
    print(f"First raw row: {rows[0]}")
    print(f"RISE is stored as {type(rows[0]['RISE']).__name__}")
    print(f"First daylight duration: {lengths[0]} minutes = {lengths[0] / 60:.2f} hours")
    print(f"Shortest: {min(lengths)} minutes; longest: {max(lengths)} minutes")
    print(f"Annual difference: {max(lengths) - min(lengths)} minutes")


if __name__ == "__main__":
    main()
