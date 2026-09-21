# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Plot a year of HKO sunrise, solar noon, sunset and daylight duration.
Run: uv run plot.py. Only the committed CSV is read; no network is used.
"""
import csv
from datetime import date, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Circle, Wedge
import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "hko-sunrise-sunset-2026.csv"
OUT = HERE / "out" / "daylight-2026.png"
INK = "#283b52"
PAPER = "#faf7f0"


def to_minutes(clock):
    """Convert HH:MM text to minutes since midnight."""
    hour, minute = map(int, clock.split(":"))
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError(f"Invalid time: {clock}")
    return hour * 60 + minute


def load_data():
    """Keep every record and fail clearly on invalid or missing dates/times."""
    days, rises, noons, sets = [], [], [], []
    with DATA.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            day = date.fromisoformat(row["YYYY-MM-DD"])
            rise = to_minutes(row["RISE"])
            noon = to_minutes(row["TRAN."])
            setting = to_minutes(row["SET"])
            if not rise < noon < setting:
                raise ValueError(f"Unexpected sun times on {day}")
            days.append(day)
            rises.append(rise)
            noons.append(noon)
            sets.append(setting)
    expected = [date(2026, 1, 1) + timedelta(days=i) for i in range(365)]
    if days != expected:
        raise ValueError("Expected all 365 dates of 2026 in order, without duplicates")
    return days, np.array(rises), np.array(noons), np.array(sets)


def sky_image(rises, noons, sets):
    """Decorative colours follow real daily boundaries, not measured sky colours.
    The intermediate stops are design choices, not twilight calculations.
    """
    times = np.linspace(0, 24, 721)
    colours = np.array([to_rgb(c) for c in
        ["#101b38", "#47466c", "#efa47c", "#bcdde7", "#fff1bd",
         "#bcdde7", "#e99aaa", "#51466d", "#101b38"]])
    pixels = np.empty((len(times), len(rises), 3))
    for i, (rise, noon, setting) in enumerate(zip(rises / 60, noons / 60, sets / 60)):
        stops = [0, rise * .72, rise, (rise + noon) / 2, noon,
                 (noon + setting) / 2, setting, setting + (24 - setting) * .35, 24]
        for channel in range(3):
            pixels[:, i, channel] = np.interp(times, stops, colours[:, channel])
    return pixels


def sun_icon(fig, left, kind):
    """Draw small vector sun icons without fonts or external image files."""
    ax = fig.add_axes([left, .839, .027, .032])
    ax.set(xlim=(-1.5, 1.5), ylim=(-1.4, 1.5), aspect="equal")
    ax.axis("off")
    if kind == "noon":
        ax.add_patch(Circle((0, 0), .58, color="#d39735"))
        angles = np.linspace(0, 2 * np.pi, 8, endpoint=False)
    else:
        ax.add_patch(Wedge((0, 0), .65, 0, 180, color="#ce805d" if kind == "rise" else "#b56e85"))
        ax.plot([-1.2, 1.2], [0, 0], color=INK, lw=1.2)
        angles = np.linspace(0, np.pi, 5)
    for angle in angles:
        ax.plot([.85 * np.cos(angle), 1.12 * np.cos(angle)],
                [.85 * np.sin(angle), 1.12 * np.sin(angle)], color=INK, lw=1)


def main():
    days, rises, noons, sets = load_data()
    minutes = sets - rises
    shortest, longest = int(min(minutes)), int(max(minutes))
    difference = longest - shortest
    x = mdates.date2num(days)
    fig = plt.figure(figsize=(12, 10), facecolor=PAPER)
    fig.text(.10, .953, "A YEAR OF DAYLIGHT", fontsize=28, weight="bold", color=INK)
    fig.text(.10, .917, "HONG KONG  /  2026", fontsize=11, color="#617084")
    fig.text(.10, .885, "A wider band means a longer day. Read the year from left to right.", fontsize=11, color=INK)
    for left, kind, label in [(.10, "rise", "Sunrise / solid"), (.36, "noon", "Solar noon / dashed"), (.65, "set", "Sunset / solid")]:
        sun_icon(fig, left, kind)
        fig.text(left + .037, .849, label, fontsize=10, color=INK)

    ax = fig.add_axes([.10, .405, .86, .412])
    ax.imshow(sky_image(rises, noons, sets), origin="lower", aspect="auto",
              extent=[x[0] - .5, x[-1] + .5, 0, 24], interpolation="nearest")
    ax.plot(days, rises / 60, color="#fff9e5", lw=1.3)
    ax.plot(days, sets / 60, color="#fff9e5", lw=1.3)
    ax.plot(days, noons / 60, color=INK, lw=1, ls=(0, (4, 4)), alpha=.8)
    for label, values, offset in [("Sunrise", rises, 9), ("Solar noon", noons, 9), ("Sunset", sets, 9)]:
        ax.annotate(label, (x[12], values[12] / 60), xytext=(0, offset), textcoords="offset points",
                    color=INK if label != "Sunset" else "white", fontsize=9, weight="bold")
    ax.set_ylim(0, 24)
    ax.set_yticks([0, 6, 12, 18, 24], ["00:00", "06:00", "12:00", "18:00", "24:00"])
    ax.set_ylabel("Time of day / Hong Kong time (UTC+8)", color=INK, labelpad=12)
    ax.set_title("01   SUNRISE TO SUNSET", loc="left", fontsize=10, color=INK, pad=12)

    small = fig.add_axes([.10, .145, .86, .16])
    small.set_facecolor(PAPER)
    small.plot(days, minutes / 60, color="#b36b40", lw=2)
    small.axhline(12, color="#9a9eaa", lw=.8, ls="--")
    small.text(x[-1] - 3, 12.10, "12 hours", ha="right", color="#617084", fontsize=8)
    for extreme in (shortest, longest):
        mask = minutes == extreme
        small.scatter(x[mask], minutes[mask] / 60, color=INK, s=10, zorder=3)
    small.set_ylim(10, 14)
    small.set_yticks([10, 12, 14])
    small.set_ylabel("Daylight / hours", color=INK, labelpad=12)
    small.set_title("02   HOW LONG IS THE DAY?", loc="left", fontsize=10, color=INK, pad=25)
    fig.text(.10, .319, f"Longest {longest // 60} h {longest % 60:02d} min   /   Shortest {shortest // 60} h {shortest % 60:02d} min   /   Difference {difference // 60} h {difference % 60:02d} min", fontsize=10, color=INK)
    for chart in (ax, small):
        chart.set_xlim(x[0] - .5, x[-1] + .5)
        chart.xaxis.set_major_locator(mdates.MonthLocator())
        chart.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        chart.tick_params(colors=INK, length=0, pad=7, labelsize=9)
        chart.spines[["top", "right"]].set_visible(False)
        chart.spines[["left", "bottom"]].set_color("#abb0b7")
    small.grid(axis="y", alpha=.15)
    fig.text(.10, .082, "Source: Hong Kong Observatory / 365 daily records / Time resolution: one minute.", fontsize=9, color="#617084")
    fig.text(.10, .059, "Sky colours are illustrative, not measured weather or twilight. Daylight is not actual sunshine duration.", fontsize=9, color="#617084")
    fig.text(.10, .036, "No smoothing applied. Small-chart dots mark every date tied for the longest or shortest day.", fontsize=9, color="#617084")
    OUT.parent.mkdir(exist_ok=True)
    fig.savefig(OUT, dpi=180, facecolor=PAPER)
    plt.close(fig)
    print(f"Saved {OUT.name}: {len(days)} days; min={shortest}, max={longest}, difference={difference} minutes")


if __name__ == "__main__":
    main()
