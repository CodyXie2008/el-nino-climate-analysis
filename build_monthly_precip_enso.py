"""Create monthly Santa Barbara precipitation records matched to seasonal ENSO."""
from __future__ import annotations

import argparse
import calendar
import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

SEASON_FOR_MONTH = {1: "DJF", 2: "JFM", 3: "FMA", 4: "MAM", 5: "AMJ", 6: "MJJ", 7: "JJA", 8: "JAS", 9: "ASO", 10: "SON", 11: "OND", 12: "NDJ"}

def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine monthly precipitation with seasonal RONI/ONI.")
    parser.add_argument("--start-year", type=int, default=1950)
    parser.add_argument("--end-year", type=int, default=2025, help="Last calendar year to include.")
    parser.add_argument("--station", default="USW00023190")
    parser.add_argument("--lcd-dir", type=Path, default=Path("data/raw_lcd"))
    parser.add_argument("--enso-dir", type=Path, default=Path("data/enso_indices"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/santa_barbara_monthly_precip_enso.csv"))
    return parser.parse_args()

def read_enso(path: Path) -> dict[tuple[int, str], float]:
    with path.open(newline="", encoding="utf-8") as file:
        return {(int(row["YR"]), row["SEAS"]): float(row["ANOM"]) for row in csv.DictReader(file)}

def parse_precipitation(value: str) -> tuple[float | None, bool]:
    value = value.strip()
    if value == "T": return 0.0, True
    if not value or value.upper() in {"M", "MM"}: return None, False
    try: return float(value), False
    except ValueError: return None, False

def monthly_precipitation(args: argparse.Namespace) -> tuple[dict[tuple[int, int], dict[str, float | int]], date]:
    totals: dict[tuple[int, int], dict[str, float | int]] = defaultdict(lambda: {"total": 0.0, "observations": 0, "missing": 0, "trace": 0})
    dates_seen: set[str] = set()
    latest_date: date | None = None
    for year in range(args.start_year, args.end_year + 1):
        path = args.lcd_dir / f"LCD_{args.station}_{year}.csv"
        if not path.exists(): raise FileNotFoundError(f"Missing LCD file: {path}")
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as file:
            for row in csv.DictReader(file):
                if row.get("REPORT_TYPE") != "SOD": continue
                date = datetime.fromisoformat(row["DATE"])
                date_id = date.date().isoformat()
                if date_id in dates_seen: raise ValueError(f"Duplicate SOD record: {date_id}")
                dates_seen.add(date_id)
                latest_date = max(latest_date, date.date()) if latest_date else date.date()
                record = totals[(date.year, date.month)]
                amount, trace = parse_precipitation(row.get("DailyPrecipitation", ""))
                if amount is None: record["missing"] += 1
                else:
                    record["total"] += amount
                    record["observations"] += 1
                    record["trace"] += int(trace)
    if latest_date is None: raise ValueError("No SOD precipitation records were found.")
    return totals, latest_date

def main() -> int:
    args = arguments()
    if args.start_year > args.end_year: raise SystemExit("--start-year must not exceed --end-year.")
    precipitation, latest_observation = monthly_precipitation(args)
    roni = read_enso(args.enso_dir / "relative_seasonal_ersstv6_roni.csv")
    oni = read_enso(args.enso_dir / "sst_seasonal_ersstv6_oni.csv")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["year", "month", "month_start", "enso_season", "roni_anom_c", "oni_anom_c", "precipitation_total_mm", "daily_observations", "days_in_month", "missing_precip_days", "trace_precip_days", "precipitation_coverage_pct"]
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields); writer.writeheader()
        for year in range(args.start_year, args.end_year + 1):
            for month in range(1, 13):
                if date(year, month, 1) > latest_observation.replace(day=1):
                    continue
                data, days, season = precipitation[(year, month)], calendar.monthrange(year, month)[1], SEASON_FOR_MONTH[month]
                writer.writerow({"year": year, "month": month, "month_start": f"{year}-{month:02d}-01", "enso_season": season, "roni_anom_c": roni.get((year, season), ""), "oni_anom_c": oni.get((year, season), ""), "precipitation_total_mm": f"{data['total']:.1f}", "daily_observations": data["observations"], "days_in_month": days, "missing_precip_days": data["missing"], "trace_precip_days": data["trace"], "precipitation_coverage_pct": f"{100 * data['observations'] / days:.1f}"})
    print(f"Created {args.output} through {latest_observation.isoformat()}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
