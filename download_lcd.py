"""Download yearly NOAA Local Climatological Data (LCD) files.

Example:
    python download_lcd.py --start-year 1999 --end-year 2026

The NOAA LCD v2 archive uses a predictable URL, so the script requests the
file directly instead of scraping each year's directory listing.
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


URL_TEMPLATE = (
    "https://www.ncei.noaa.gov/oa/local-climatological-data/"
    "v2/access/{year}/LCD_{station}_{year}.csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download yearly NOAA LCD v2 CSV files for one station."
    )
    parser.add_argument("--station", default="USW00023190", help="NOAA station ID")
    parser.add_argument("--start-year", type=int, default=1937)
    parser.add_argument("--end-year", type=int, default=date.today().year)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data") / "raw_lcd",
        help="Directory for CSV files and download_manifest.csv",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Download files that already exist"
    )
    return parser.parse_args()


def fetch(url: str, destination: Path) -> tuple[str, int | str]:
    """Download URL atomically and return (status, byte_count_or_reason)."""
    request = Request(url, headers={"User-Agent": "lcd-research-downloader/1.0"})
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output)
    except HTTPError as error:
        temporary.unlink(missing_ok=True)
        if error.code == 404:
            return "not_available", error.code
        return "http_error", error.code
    except URLError as error:
        temporary.unlink(missing_ok=True)
        return "network_error", str(error.reason)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        return "file_error", str(error)

    # A successful NOAA CSV begins with its column header.  This catches an
    # accidental HTML/error payload before it is kept as research data.
    with temporary.open("rb") as downloaded:
        first_line = downloaded.readline(4096).decode("utf-8-sig", errors="replace")
    if "DATE" not in first_line or "," not in first_line:
        temporary.unlink(missing_ok=True)
        return "invalid_response", "CSV header not found"

    size = temporary.stat().st_size
    temporary.replace(destination)
    return "downloaded", size


def main() -> int:
    args = parse_args()
    if args.start_year > args.end_year:
        print("Error: --start-year must not exceed --end-year.", file=sys.stderr)
        return 2
    if args.end_year > date.today().year:
        print("Error: --end-year cannot be in the future.", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "download_manifest.csv"
    rows: list[dict[str, str | int]] = []

    for year in range(args.start_year, args.end_year + 1):
        filename = f"LCD_{args.station}_{year}.csv"
        destination = args.output_dir / filename
        url = URL_TEMPLATE.format(station=args.station, year=year)

        if destination.exists() and not args.overwrite:
            status, detail = "skipped_existing", destination.stat().st_size
        else:
            print(f"{year}: requesting {url}")
            status, detail = fetch(url, destination)
            # Be gentle with the public archive when requesting many years.
            time.sleep(0.2)

        print(f"  {status}: {detail}")
        rows.append({"year": year, "filename": filename, "url": url,
                     "status": status, "detail": detail})

    with manifest_path.open("w", newline="", encoding="utf-8") as manifest:
        writer = csv.DictWriter(
            manifest, fieldnames=["year", "filename", "url", "status", "detail"]
        )
        writer.writeheader()
        writer.writerows(rows)

    downloaded = sum(row["status"] == "downloaded" for row in rows)
    unavailable = sum(row["status"] == "not_available" for row in rows)
    print(f"\nDone: {downloaded} downloaded; {unavailable} not available.")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
