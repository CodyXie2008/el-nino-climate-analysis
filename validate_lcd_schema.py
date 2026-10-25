"""Compare downloaded NOAA LCD CSV schemas with a reference-year file.

CSV has no declared data types, so this script infers types from the values in
the reference file.  It then checks that values in each year's corresponding
column use only those same observed types.  Empty cells are allowed in every
column because LCD legitimately omits many measurements.

Example:
    python validate_lcd_schema.py --reference-year 2026
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ISO_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
INTEGER = re.compile(r"^[+-]?\d+$")
NUMBER = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate NOAA LCD CSV columns against a reference year."
    )
    parser.add_argument("--station", default="USW00023190")
    parser.add_argument("--reference-year", type=int, default=2026)
    parser.add_argument("--data-dir", type=Path, default=Path("data") / "raw_lcd")
    parser.add_argument("--start-year", type=int, help="First data year to validate")
    parser.add_argument("--end-year", type=int, help="Last data year to validate")
    return parser.parse_args()


def value_type(value: str) -> str | None:
    """Return the broad CSV value type, or None for a legitimate empty cell."""
    value = value.strip()
    if not value:
        return None
    if ISO_DATETIME.fullmatch(value):
        return "datetime"
    if INTEGER.fullmatch(value):
        return "integer"
    if NUMBER.fullmatch(value):
        return "number"
    return "text"


def inspect_csv(path: Path) -> tuple[list[str], dict[str, set[str]], int, int]:
    """Return header, observed types, row count, and malformed-row count."""
    types: dict[str, set[str]] = defaultdict(set)
    row_count = malformed_rows = 0
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as source:
        reader = csv.reader(source)
        try:
            header = next(reader)
        except StopIteration:
            return [], types, row_count, 1
        for row in reader:
            row_count += 1
            if len(row) != len(header):
                malformed_rows += 1
                continue
            for column, value in zip(header, row):
                observed = value_type(value)
                if observed is not None:
                    types[column].add(observed)
    return header, types, row_count, malformed_rows


def compact(items: list[str], limit: int = 12) -> str:
    if not items:
        return ""
    shown = items[:limit]
    return "; ".join(shown) + (f"; +{len(items) - limit} more" if len(items) > limit else "")


def main() -> int:
    args = parse_args()
    pattern = f"LCD_{args.station}_*.csv"
    files = sorted(args.data_dir.glob(pattern))
    if args.start_year is not None or args.end_year is not None:
        start = args.start_year if args.start_year is not None else -float("inf")
        end = args.end_year if args.end_year is not None else float("inf")
        if start > end:
            raise SystemExit("--start-year must not exceed --end-year.")
        files = [
            path for path in files
            if start <= int(path.stem.rsplit("_", 1)[1]) <= end
        ]
    reference = args.data_dir / f"LCD_{args.station}_{args.reference_year}.csv"
    manifest = args.data_dir / "download_manifest.csv"
    if not reference.exists():
        raise SystemExit(f"Reference file not found: {reference}")
    if not manifest.exists():
        raise SystemExit(f"Manifest not found: {manifest}")

    reference_header, reference_types, _, reference_bad_rows = inspect_csv(reference)
    if not reference_header or reference_bad_rows:
        raise SystemExit("Reference file has no valid header or malformed rows.")
    reference_columns = set(reference_header)

    results: dict[str, dict[str, str | int]] = {}
    for path in files:
        header, observed_types, rows, malformed_rows = inspect_csv(path)
        columns = set(header)
        missing = sorted(reference_columns - columns)
        extra = sorted(columns - reference_columns)
        type_mismatches: list[str] = []
        for column in sorted(reference_columns & columns):
            # A column that is completely empty in 2026 has no observable type
            # to compare; its presence is still checked above.
            allowed = set(reference_types.get(column, set()))
            # Decimal-capable CSV fields may happen to contain only whole
            # numbers in one year; an integer is valid wherever a number is.
            if "number" in allowed:
                allowed.add("integer")
            unexpected = observed_types.get(column, set()) - allowed
            if allowed and unexpected:
                type_mismatches.append(
                    f"{column}: expected {'/'.join(sorted(allowed))}, got {'/'.join(sorted(unexpected))}"
                )

        status = "ok" if not (missing or extra or type_mismatches or malformed_rows) else "review"
        results[path.name] = {
            "schema_reference": str(args.reference_year),
            "schema_status": status,
            "schema_rows_checked": rows,
            "schema_missing_columns": compact(missing),
            "schema_extra_columns": compact(extra),
            "schema_type_mismatches": compact(type_mismatches),
            "schema_malformed_rows": malformed_rows,
        }

    with manifest.open("r", newline="", encoding="utf-8-sig") as source:
        existing_rows = list(csv.DictReader(source))
    base_fields = list(existing_rows[0].keys()) if existing_rows else [
        "year", "filename", "url", "status", "detail"
    ]
    schema_fields = [
        "schema_reference", "schema_status", "schema_rows_checked",
        "schema_missing_columns", "schema_extra_columns", "schema_type_mismatches",
        "schema_malformed_rows",
    ]
    fieldnames = base_fields + [field for field in schema_fields if field not in base_fields]

    with manifest.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing_rows:
            row.update(results.get(row["filename"], {}))
            writer.writerow(row)

    counts = Counter(str(result["schema_status"]) for result in results.values())
    print(f"Reference: {reference.name} ({len(reference_header)} columns)")
    print(f"Checked: {len(results)} files; ok: {counts['ok']}; review: {counts['review']}")
    print(f"Updated manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
