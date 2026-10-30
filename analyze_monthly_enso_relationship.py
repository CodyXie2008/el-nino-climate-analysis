"""Explore month-specific relationships between Santa Barbara precipitation and RONI."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


INPUT = Path("data/processed/santa_barbara_monthly_precip_enso.csv")
FIGURE = Path("figures/monthly_roni_precipitation_relationships.png")
SUMMARY = Path("data/processed/monthly_roni_precipitation_correlations.csv")
BASELINE_START, BASELINE_END = 1991, 2020
MIN_COVERAGE_PCT = 90.0
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def pearson_r(x: list[float], y: list[float]) -> float:
    mean_x, mean_y = sum(x) / len(x), sum(y) / len(y)
    numerator = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
    denominator = math.sqrt(sum((a - mean_x) ** 2 for a in x) * sum((b - mean_y) ** 2 for b in y))
    return numerator / denominator if denominator else float("nan")


def main() -> None:
    with INPUT.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    normals: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        if (BASELINE_START <= int(row["year"]) <= BASELINE_END
                and float(row["precipitation_coverage_pct"]) >= MIN_COVERAGE_PCT):
            normals[int(row["month"])].append(float(row["precipitation_total_mm"]))
    normal = {month: sum(values) / len(values) for month, values in normals.items()}

    grouped: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for row in rows:
        if float(row["precipitation_coverage_pct"]) < MIN_COVERAGE_PCT or not row["roni_anom_c"]:
            continue
        month = int(row["month"])
        anomaly = float(row["precipitation_total_mm"]) - normal[month]
        grouped[month].append((float(row["roni_anom_c"]), anomaly))

    all_anomalies = [value for pairs in grouped.values() for _, value in pairs]
    x_limit = 2.7
    y_low, y_high = min(all_anomalies), max(all_anomalies)
    y_pad = (y_high - y_low) * 0.08
    figure, axes = plt.subplots(3, 4, figsize=(15, 10), sharex=True, sharey=True)
    summary_rows = []
    for month, axis in enumerate(axes.flat, start=1):
        pairs = grouped[month]
        x, y = zip(*pairs)
        correlation = pearson_r(list(x), list(y))
        axis.scatter(x, y, s=19, color="#1f77b4", alpha=0.72, edgecolors="none")
        slope, intercept = __import__("numpy").polyfit(x, y, 1)
        axis.plot([-x_limit, x_limit], [slope * -x_limit + intercept, slope * x_limit + intercept], color="#c43c39", linewidth=1.2)
        axis.axhline(0, color="black", linestyle="--", linewidth=0.75)
        axis.axvline(0, color="black", linestyle="--", linewidth=0.75)
        axis.set_title(MONTHS[month - 1], fontsize=12)
        axis.text(0.03, 0.94, f"n = {len(pairs)}\nr = {correlation:.2f}", transform=axis.transAxes, va="top", fontsize=9)
        axis.set_xlim(-x_limit, x_limit)
        axis.set_ylim(y_low - y_pad, y_high + y_pad)
        summary_rows.append({"month": month, "month_name": MONTHS[month - 1], "n": len(pairs), "pearson_r": f"{correlation:.4f}", "slope_mm_per_c": f"{slope:.4f}"})

    figure.supxlabel("RONI (°C)", fontsize=13)
    figure.supylabel("Monthly precipitation anomaly (mm/month)", fontsize=13)
    figure.suptitle("Santa Barbara precipitation anomaly vs. RONI, by calendar month", fontsize=16, y=0.995)
    figure.text(0.5, 0.008, "Precipitation baseline: 1991–2020 same-month mean; months with <90% daily coverage excluded", ha="center", fontsize=9)
    figure.tight_layout(rect=(0.03, 0.035, 1, 0.97))
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=220, bbox_inches="tight")
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=summary_rows[0].keys())
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"Saved {FIGURE} and {SUMMARY}")


if __name__ == "__main__":
    main()
