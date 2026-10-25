# Santa Barbara NOAA LCD downloader

This project downloads annual NOAA Local Climatological Data (LCD) CSV files
for Santa Barbara Municipal Airport, station `USW00023190`.

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

## Validate column types

After downloading, compare every CSV's headers and observed value types with
the 2026 file and write the results into the same manifest:

```powershell
python .\validate_lcd_schema.py --reference-year 2026
```

For a very large archive, it can be run in year ranges; each range updates the
same manifest without erasing earlier results:

```powershell
python .\validate_lcd_schema.py --start-year 1937 --end-year 1949
```

`schema_status` is `ok` when the file has the same columns, no malformed CSV
rows, and no values of a type absent from the corresponding 2026 column.
Because CSV files do not store declared data types, blank cells are permitted
and types are inferred from non-empty values.
