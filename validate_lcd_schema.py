"""Check that yearly NOAA LCD CSV files have the same ordered header as 2026.

Example:
    python validate_lcd_schema.py --reference-year 2026
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare NOAA LCD CSV column names and order with a reference year."
    )
    parser.add_argument("--station", default="USW00023190")
    parser.add_argument("--reference-year", type=int, default=2026)
    parser.add_argument("--data-dir", type=Path, default=Path("data") / "raw_lcd")
    return parser.parse_args()


def read_header(path: Path) -> list[str]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as source:
        reader = csv.reader(source)
        return next(reader, [])


def describe_difference(reference: list[str], actual: list[str]) -> str:
    for position, (expected, found) in enumerate(zip(reference, actual), start=1):
        if expected != found:
            return f"column {position}: expected {expected!r}, found {found!r}"
    if len(actual) < len(reference):
        return f"column {len(actual) + 1}: expected {reference[len(actual)]!r}, found no column"
    return f"column {len(reference) + 1}: expected no column, found {actual[len(reference)]!r}"


def main() -> int:
    args = parse_args()
    reference = args.data_dir / f"LCD_{args.station}_{args.reference_year}.csv"
    manifest = args.data_dir / "download_manifest.csv"
    if not reference.exists() or not manifest.exists():
        raise SystemExit("Reference CSV or download_manifest.csv was not found.")
    reference_header = read_header(reference)
    if not reference_header:
        raise SystemExit(f"Reference CSV has no header: {reference}")

    results: dict[str, dict[str, str | int]] = {}
    for path in sorted(args.data_dir.glob(f"LCD_{args.station}_*.csv")):
        header = read_header(path)
        matches = header == reference_header
        results[path.name] = {
            "header_reference": str(args.reference_year),
            "header_status": "match" if matches else "different",
            "header_column_count": len(header),
            "header_first_difference": "" if matches else describe_difference(reference_header, header),
        }

    with manifest.open("r", newline="", encoding="utf-8-sig") as source:
        existing_rows = list(csv.DictReader(source))
    fieldnames = ["year", "filename", "url", "status", "detail", "header_reference",
                  "header_status", "header_column_count", "header_first_difference"]

    with manifest.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing_rows:
            clean_row = {field: row.get(field, "") for field in fieldnames}
            clean_row.update(results.get(row["filename"], {}))
            writer.writerow(clean_row)

    matching = sum(result["header_status"] == "match" for result in results.values())
    print(f"Reference: {reference.name} ({len(reference_header)} columns)")
    print(f"Checked: {len(results)} files; match: {matching}; different: {len(results) - matching}")
    print(f"Updated manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
