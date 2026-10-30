"""Analyze the likelihood of wetter Santa Barbara DJF seasons by RONI phase."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


INPUT = Path("data/processed/santa_barbara_monthly_precip_enso.csv")
SEASONAL_DATA = Path("data/processed/djf_precipitation_roni.csv")
SUMMARY = Path("data/processed/djf_roni_phase_summary.csv")
FIGURE = Path("figures/djf_roni_precipitation_probability.png")
BASELINE_START, BASELINE_END = 1991, 2020
MIN_COVERAGE_PCT = 90.0
PHASES = ["La Nina", "Neutral", "El Nino"]


def phase(value: float) -> str:
    if value >= 0.5:
        return "El Nino"
    if value <= -0.5:
        return "La Nina"
    return "Neutral"


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if not total:
        return float("nan"), float("nan")
    p = successes / total
    denominator = 1 + z ** 2 / total
    center = (p + z ** 2 / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z ** 2 / (4 * total ** 2)) / denominator
    return center - margin, center + margin


def pearson_r(x: list[float], y: list[float]) -> float:
    mx, my = np.mean(x), np.mean(y)
    denominator = math.sqrt(sum((value - mx) ** 2 for value in x) * sum((value - my) ** 2 for value in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / denominator


def main() -> None:
    with INPUT.open(newline="", encoding="utf-8") as file:
        monthly = list(csv.DictReader(file))
    lookup = {(int(row["year"]), int(row["month"])): row for row in monthly}

    normals: dict[int, list[float]] = defaultdict(list)
    for row in monthly:
        if (BASELINE_START <= int(row["year"]) <= BASELINE_END
                and float(row["precipitation_coverage_pct"]) >= MIN_COVERAGE_PCT):
            normals[int(row["month"])].append(float(row["precipitation_total_mm"]))
    normal = {month: np.mean(values) for month, values in normals.items()}

    seasons = []
    for year in range(1951, max(int(row["year"]) for row in monthly) + 1):
        months = [lookup.get((year - 1, 12)), lookup.get((year, 1)), lookup.get((year, 2))]
        if any(row is None for row in months):
            continue
        if any(float(row["precipitation_coverage_pct"]) < MIN_COVERAGE_PCT for row in months):
            continue
        roni = months[1]["roni_anom_c"]  # January maps to DJF of the same labeled year.
        if not roni:
            continue
        mean_precip = np.mean([float(row["precipitation_total_mm"]) for row in months])
        mean_anomaly = np.mean([float(row["precipitation_total_mm"]) - normal[int(row["month"])] for row in months])
        seasons.append({"djf_year": year, "roni_djf_c": float(roni), "roni_phase": phase(float(roni)),
                        "djf_mean_precipitation_mm_month": mean_precip,
                        "djf_mean_precipitation_anomaly_mm_month": mean_anomaly,
                        "wetter_than_normal": int(mean_anomaly > 0)})

    upper_quartile = float(np.percentile([row["djf_mean_precipitation_anomaly_mm_month"] for row in seasons], 75))
    for row in seasons:
        row["very_wet_winter"] = int(row["djf_mean_precipitation_anomaly_mm_month"] > upper_quartile)

    SEASONAL_DATA.parent.mkdir(parents=True, exist_ok=True)
    with SEASONAL_DATA.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=seasons[0].keys())
        writer.writeheader(); writer.writerows(seasons)

    summary = []
    for group in PHASES:
        values = [row for row in seasons if row["roni_phase"] == group]
        wet = sum(row["wetter_than_normal"] for row in values)
        very_wet = sum(row["very_wet_winter"] for row in values)
        low, high = wilson_interval(wet, len(values))
        summary.append({"roni_phase": group, "n": len(values),
                        "mean_anomaly_mm_month": f"{np.mean([row['djf_mean_precipitation_anomaly_mm_month'] for row in values]):.2f}",
                        "median_anomaly_mm_month": f"{np.median([row['djf_mean_precipitation_anomaly_mm_month'] for row in values]):.2f}",
                        "wetter_than_normal_n": wet, "wetter_than_normal_probability": f"{wet / len(values):.3f}",
                        "wetter_than_normal_ci_low": f"{low:.3f}", "wetter_than_normal_ci_high": f"{high:.3f}",
                        "very_wet_n": very_wet, "very_wet_probability": f"{very_wet / len(values):.3f}"})
    with SUMMARY.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=summary[0].keys())
        writer.writeheader(); writer.writerows(summary)

    colors = {"La Nina": "#4c78a8", "Neutral": "#8c8c8c", "El Nino": "#e45756"}
    figure, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    values_by_phase = [[row["djf_mean_precipitation_anomaly_mm_month"] for row in seasons if row["roni_phase"] == group] for group in PHASES]
    box = axes[0].boxplot(values_by_phase, tick_labels=PHASES, patch_artist=True, medianprops={"color": "black"})
    for patch, group in zip(box["boxes"], PHASES): patch.set_facecolor(colors[group]); patch.set_alpha(0.55)
    for index, group in enumerate(PHASES, 1):
        values = values_by_phase[index - 1]
        jitter = np.linspace(-0.12, 0.12, len(values))
        axes[0].scatter(index + jitter, values, color=colors[group], s=26, alpha=0.8)
    axes[0].axhline(0, color="black", linestyle="--", linewidth=0.8)
    axes[0].set_title("DJF precipitation anomaly by RONI phase")
    axes[0].set_ylabel("Mean monthly anomaly (mm/month)")

    probabilities = [float(row["wetter_than_normal_probability"]) for row in summary]
    errors = [[p - float(row["wetter_than_normal_ci_low"]) for p, row in zip(probabilities, summary)],
              [float(row["wetter_than_normal_ci_high"]) - p for p, row in zip(probabilities, summary)]]
    axes[1].bar(PHASES, probabilities, yerr=errors, color=[colors[group] for group in PHASES], capsize=5, alpha=0.8)
    axes[1].axhline(0.5, color="black", linestyle="--", linewidth=0.8)
    axes[1].set_ylim(0, 1)
    axes[1].set_title("Probability of a wetter-than-normal DJF")
    axes[1].set_ylabel("Probability (Wilson 95% CI)")
    for index, row in enumerate(summary): axes[1].text(index, probabilities[index] + 0.05, f"n={row['n']}", ha="center")

    x = [row["roni_djf_c"] for row in seasons]
    y = [row["djf_mean_precipitation_anomaly_mm_month"] for row in seasons]
    axes[2].scatter(x, y, color="#1f77b4", alpha=0.8)
    slope, intercept = np.polyfit(x, y, 1)
    xs = np.array([min(x), max(x)])
    axes[2].plot(xs, slope * xs + intercept, color="#c43c39")
    axes[2].axhline(0, color="black", linestyle="--", linewidth=0.8)
    axes[2].axvline(0, color="black", linestyle="--", linewidth=0.8)
    axes[2].set_title(f"Continuous DJF relationship (r = {pearson_r(x, y):.2f})")
    axes[2].set_xlabel("DJF RONI (°C)")
    axes[2].set_ylabel("Mean monthly anomaly (mm/month)")

    figure.suptitle("Santa Barbara DJF precipitation and RONI, 1951–present", fontsize=16)
    figure.text(0.5, 0.01, "Precipitation baseline: 1991–2020; every DJF month requires ≥90% daily coverage", ha="center", fontsize=9)
    figure.tight_layout(rect=(0, 0.04, 1, 0.92))
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=220, bbox_inches="tight")
    print(f"Saved {SEASONAL_DATA}, {SUMMARY}, and {FIGURE} ({len(seasons)} valid DJF seasons)")


if __name__ == "__main__":
    main()
