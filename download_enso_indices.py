"""Download NOAA CPC ENSO SST indices and convert their tables to CSV.

Sources are the CPC indices directory.  Both OISST and ERSST monthly series
are retained because they are distinct source products.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.request import Request, urlopen


BASE_URL = "https://www.cpc.ncep.noaa.gov/data/indices/"
DATASETS = {
    "relative_weekly_oisst": ("rel_wksst9120.txt", "weekly_relative"),
    "relative_monthly_oisst": ("rel_mthsst9120.txt", "table"),
    "relative_monthly_ersstv6": ("Rnino34.ascii.txt", "table"),
    "relative_seasonal_ersstv6_roni": ("RONI.ascii.txt", "table"),
    "sst_weekly_oisst": ("wksst9120.for", "weekly_sst"),
    "sst_monthly_oisst": ("sstoi.indices", "monthly_sst_oisst"),
    "sst_monthly_ersstv6": ("detrend.nino34.ascii.txt", "table"),
    "sst_seasonal_ersstv6_oni": ("oni.ascii.txt", "table"),
}
FLOAT = re.compile(r"[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)")
DATE = re.compile(r"^\d{2}[A-Z]{3}\d{4}$")


def parse_table(text: str, kind: str) -> tuple[list[str], list[list[str]]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if kind == "weekly_relative":
        rows = [line.split() for line in lines if DATE.match(line.split()[0])]
        return ["week_centered", "nino12_relative_ssta", "nino3_relative_ssta",
                "nino34_relative_ssta", "nino4_relative_ssta"], rows
    if kind == "weekly_sst":
        rows = []
        for line in lines:
            parts = line.split(maxsplit=1)
            if len(parts) == 2 and DATE.match(parts[0]):
                rows.append([parts[0], *FLOAT.findall(parts[1])])
        return ["week_centered", "nino12_sst", "nino12_ssta", "nino3_sst", "nino3_ssta",
                "nino34_sst", "nino34_ssta", "nino4_sst", "nino4_ssta"], rows
    if kind == "monthly_sst_oisst":
        rows = [line.split() for line in lines[1:] if len(line.split()) == 10]
        return ["year", "month", "nino12_sst", "nino12_ssta", "nino3_sst", "nino3_ssta",
                "nino4_sst", "nino4_ssta", "nino34_sst", "nino34_ssta"], rows
    return lines[0].split(), [line.split() for line in lines[1:]]


def main() -> int:
    output_dir = Path("data") / "enso_indices"
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows = []

    for name, (remote_name, parser) in DATASETS.items():
        url = BASE_URL + remote_name
        print(f"Downloading {remote_name}")
        request = Request(url, headers={"User-Agent": "enso-research-downloader/1.0"})
        with urlopen(request, timeout=60) as response:
            content = response.read()
        raw_path = raw_dir / remote_name
        raw_path.write_bytes(content)
        headers, rows = parse_table(content.decode("utf-8", errors="replace"), parser)
        csv_path = output_dir / f"{name}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow(headers)
            writer.writerows(rows)
        manifest_rows.append({"dataset": name, "frequency": name.split("_")[1],
                              "source_file": remote_name, "source_url": url,
                              "csv_file": csv_path.name, "rows": len(rows),
                              "columns": len(headers)})

    with (output_dir / "download_manifest.csv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=manifest_rows[0].keys())
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(f"Created {len(manifest_rows)} CSV files in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
