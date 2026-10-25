# Santa Barbara NOAA LCD downloader

This project downloads annual NOAA Local Climatological Data (LCD) CSV files
for Santa Barbara Municipal Airport, station `USW00023190`.

## Data included in this repository

The downloaded data are intentionally retained in this repository for
reproducibility:

- `data/raw_lcd/` — annual Santa Barbara Municipal Airport LCD files for
  1937–2026, plus `download_manifest.csv`.
- `data/enso_indices/` — CPC ENSO SST/Relative SST CSV conversions, source
  files, and a download manifest.

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

## Run it

Python 3.9+ is sufficient; no third-party packages are needed.

```powershell
# Small test: download 1937 only
python .\download_lcd.py --start-year 1937 --end-year 1937

# Download the full study period
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

## Download ENSO sea-surface-temperature indices

```powershell
python .\download_enso_indices.py
```

This downloads the eight relevant NOAA CPC source files and converts them to
CSV in `data/enso_indices/`: Relative SST and SST at weekly, monthly, and
seasonal frequencies. Raw source files are retained in `data/enso_indices/raw/`.
