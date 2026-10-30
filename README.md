# El Niño and Santa Barbara Climate

This repository contains a reproducible dataset for studying the relationship
between El Niño–Southern Oscillation (ENSO) conditions and local weather in
Santa Barbara, California.

The study location is **Santa Barbara Municipal Airport** (`USW00023190`).
The project combines the station's NOAA Local Climatological Data (LCD) with
NOAA Climate Prediction Center (CPC) ENSO sea-surface-temperature indices.

## Research focus

The data support questions such as:

- How do Santa Barbara precipitation and temperature vary during El Niño and
  La Niña conditions?
- Do large positive or negative Niño 3.4 / ONI / RONI values coincide with
  unusually wet, dry, warm, or cool periods locally?
- Does the relationship change when using weekly, monthly, or seasonal ENSO
  indicators?

## Included data

The downloaded data are intentionally retained in this repository for
reproducibility:

- `data/raw_lcd/` — annual Santa Barbara Municipal Airport LCD files for
  1937–2026, plus `download_manifest.csv`.
- `data/enso_indices/` — CPC ENSO SST/Relative SST CSV conversions, source
  files, and a download manifest.

### Dataset layout

```text
data/
├── raw_lcd/                         # 1937–2026 Santa Barbara LCD CSV files
│   └── download_manifest.csv         # Retrieval and header-validation results
└── enso_indices/
    ├── relative_weekly_oisst.csv
    ├── relative_monthly_oisst.csv
    ├── relative_monthly_ersstv6.csv
    ├── relative_seasonal_ersstv6_roni.csv
    ├── sst_weekly_oisst.csv
    ├── sst_monthly_oisst.csv
    ├── sst_monthly_ersstv6.csv
    ├── sst_seasonal_ersstv6_oni.csv
    ├── download_manifest.csv
    └── raw/                          # Original files downloaded from CPC
```

For a monthly Santa Barbara analysis, useful LCD fields include
`DailyPrecipitation`, `DailyAverageDryBulbTemperature`,
`DailyMaximumDryBulbTemperature`, and `DailyMinimumDryBulbTemperature`.
Aggregate the daily observations to the same time scale as the chosen ENSO
index before comparing them.

### Official download sources

- Santa Barbara LCD archive: [NOAA NCEI LCD v2 access directory](https://www.ncei.noaa.gov/oa/local-climatological-data/v2/access/). Each yearly file uses the direct pattern shown below.
- ENSO index catalogue: [NOAA CPC Monthly Atmospheric & SST Indices](https://www.cpc.ncep.noaa.gov/data/indices/).
- Relative SST: [weekly OISST](https://www.cpc.ncep.noaa.gov/data/indices/rel_wksst9120.txt), [monthly OISST](https://www.cpc.ncep.noaa.gov/data/indices/rel_mthsst9120.txt), [monthly ERSSTv6](https://www.cpc.ncep.noaa.gov/data/indices/Rnino34.ascii.txt), and [seasonal RONI](https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt).
- SST: [weekly OISST](https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for), [monthly OISST](https://www.cpc.ncep.noaa.gov/data/indices/sstoi.indices), [monthly ERSSTv6](https://www.cpc.ncep.noaa.gov/data/indices/detrend.nino34.ascii.txt), and [seasonal ONI](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt).

NOAA's LCD v2 archive follows this direct URL pattern:

```text
https://www.ncei.noaa.gov/oa/local-climatological-data/v2/access/{YEAR}/LCD_USW00023190_{YEAR}.csv
```

Therefore the downloader requests each year's file directly; it does not need
to load or search the large directory page.

## Reproduce the data download

Python 3.9+ is sufficient; no third-party packages are needed.

```powershell
# Small test: download 1937 only
python .\download_lcd.py --start-year 1937 --end-year 1937

# Download the full LCD study period
python .\download_lcd.py --start-year 1937 --end-year 2026
```

Files are saved to `data/raw_lcd/`.  The script also creates
`data/raw_lcd/download_manifest.csv`, which records every requested URL and
whether it was downloaded, already present, or unavailable (HTTP 404).

To download an existing file again, add `--overwrite`.  To use a different
station, provide `--station YOUR_STATION_ID`.

The current year's file can be incomplete because the year is still in
progress.  Preserve the manifest with your analysis so the data retrieval is
reproducible.

## Validate column headers

After downloading, compare every CSV's header names and their exact order with
the 2026 file and write the results into the same manifest:

```powershell
python .\validate_lcd_schema.py --reference-year 2026
```

`header_status` is `match` only when every header is identical and in the same
position as the 2026 template—for example, column 1 is `STATION`, column 2 is
`DATE`, and so on. If not, `header_first_difference` gives the first mismatch.

### Download ENSO sea-surface-temperature indices

```powershell
python .\download_enso_indices.py
```

This downloads the eight relevant NOAA CPC source files and converts them to
CSV in `data/enso_indices/`: Relative SST and SST at weekly, monthly, and
seasonal frequencies. Raw source files are retained in `data/enso_indices/raw/`.

## Build the monthly precipitation–ENSO analysis table

```powershell
python .\build_monthly_precip_enso.py
```

This creates `data/processed/santa_barbara_monthly_precip_enso.csv` for
1950–2025. It sums `DailyPrecipitation` from daily-summary (`SOD`) records by
month and matches each month to the CPC three-month season centered on it:
January → DJF, February → JFM, through December → NDJ. The output contains
seasonal RONI and ONI anomalies plus coverage and trace-precipitation fields.

To include the latest available observations from the still-in-progress 2026
file, run:

```powershell
python .\build_monthly_precip_enso.py --end-year 2026
```

The script stops at the most recent available daily observation rather than
creating rows for future months. Newly completed CPC seasonal values can lag
behind the monthly precipitation release, so the newest `roni_anom_c` and
`oni_anom_c` cells may remain blank until CPC publishes them.

## Plot monthly precipitation and ENSO

```powershell
python .\plot_monthly_precip_enso.py
```

This creates `figures/monthly_precip_anomaly_roni.png`. The upper panel shows
monthly total-precipitation anomalies against the same calendar month’s
1991–2020 mean. The lower panel shows the matching seasonal RONI value. Months
with less than 90% daily precipitation coverage are excluded.

See [the monthly time-series notes](docs/monthly_precip_anomaly_roni.md)
for the method, interpretation, and an explanation of precipitation-data gaps.

## Explore the relationship by calendar month

```powershell
python .\analyze_monthly_enso_relationship.py
```

This creates a 12-panel scatterplot, one panel for each calendar month, plus
`data/processed/monthly_roni_precipitation_correlations.csv`. Each panel
reports its sample size and Pearson correlation; it is exploratory evidence,
not a causal estimate.

See [the month-by-month scatterplot notes](docs/monthly_roni_precipitation_relationships.md)
for how each panel is constructed and interpreted.

## Analyze winter ENSO probability

```powershell
python .\analyze_djf_enso_probability.py
```

This matches DJF RONI with the mean of December–February precipitation
anomalies. It creates seasonal data, phase summaries, and a three-panel figure
comparing El Niño, neutral, and La Niña conditions.

The full statistical design and formulas are in
[DJF RONI precipitation methodology](docs/djf_roni_precipitation_model.md).

## Notes for interpretation

- **ONI** is the seasonal Niño 3.4 SST anomaly; **RONI** is its relative-SST
  counterpart.
- The present calendar year's LCD file is incomplete until the year ends.
- The source files are retained alongside the CSV conversions so every
  transformation can be checked against NOAA's original publication.
