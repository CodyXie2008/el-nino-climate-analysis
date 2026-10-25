"""Plot Santa Barbara monthly precipitation anomalies alongside RONI."""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt


INPUT = Path("data/processed/santa_barbara_monthly_precip_enso.csv")
OUTPUT = Path("figures/monthly_precip_anomaly_roni.png")
BASELINE_START, BASELINE_END = 1991, 2020
MIN_COVERAGE_PCT = 90.0


def main() -> None:
    with INPUT.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    normals: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        if (BASELINE_START <= int(row["year"]) <= BASELINE_END
                and float(row["precipitation_coverage_pct"]) >= MIN_COVERAGE_PCT):
            normals[int(row["month"])].append(float(row["precipitation_total_mm"]))
    monthly_normal = {month: sum(values) / len(values) for month, values in normals.items()}

    dates, precipitation_anomaly, roni = [], [], []
    valid_precipitation_months = valid_roni_months = 0
    for row in rows:
        month = int(row["month"])
        dates.append(datetime.fromisoformat(row["month_start"]))
        if float(row["precipitation_coverage_pct"]) < MIN_COVERAGE_PCT:
            precipitation_anomaly.append(float("nan"))
        else:
            precipitation_anomaly.append(float(row["precipitation_total_mm"]) - monthly_normal[month])
            valid_precipitation_months += 1
        if row["roni_anom_c"]:
            roni.append(float(row["roni_anom_c"]))
            valid_roni_months += 1
        else:
            roni.append(float("nan"))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    figure, (top, bottom) = plt.subplots(
        2, 1, figsize=(13, 7.5), sharex=True, gridspec_kw={"hspace": 0.14}
    )
    blue = "#1f77b4"
    for axis, values, ylabel in (
        (top, precipitation_anomaly, "Monthly precipitation anomaly\nin Santa Barbara (mm/month)"),
        (bottom, roni, "RONI (°C)"),
    ):
        axis.plot(dates, values, color=blue, linewidth=1.0)
        axis.axhline(0, color="black", linestyle="--", linewidth=1.1)
        axis.set_ylabel(ylabel, fontsize=14)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(labelsize=11)

    bottom.set_xlabel("Time (months)", fontsize=14)
    bottom.xaxis.set_major_locator(mdates.YearLocator(5))
    bottom.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    figure.suptitle("Santa Barbara monthly precipitation anomaly and RONI", fontsize=16, y=0.98)
    figure.text(
        0.5, 0.01,
        "Precipitation anomaly baseline: 1991–2020 same-month mean; months with <90% daily coverage excluded",
        ha="center", fontsize=9,
    )
    figure.savefig(OUTPUT, dpi=220, bbox_inches="tight")
    print(f"Saved {OUTPUT}: {valid_precipitation_months} precipitation months; {valid_roni_months} RONI months")


if __name__ == "__main__":
    main()
