# Monthly precipitation anomaly and RONI time series

![Monthly precipitation anomaly and RONI](../figures/monthly_precip_anomaly_roni.png)

## Purpose

This figure provides the project’s complete monthly historical context. It
places local Santa Barbara precipitation anomalies above the independently
published RONI series on a shared time axis from 1950 to the latest available
month. It is descriptive, not a causal model.

## Variables and mathematical definitions

Let \(p_{y,m,d}\) be usable daily precipitation for year \(y\), month \(m\),
and day \(d\). Monthly total precipitation is:

\[
P_{y,m}=\sum_{d=1}^{D_{y,m}}p_{y,m,d}
\]

where \(D_{y,m}\) is the number of calendar days in the month. `T` (trace)
precipitation is retained as a trace-day count and contributes 0 mm to this
sum. Missing values are not treated as zero.

The same-month 1991–2020 normal is:

\[
\overline{P}_{m}^{1991\text{–}2020}
=\frac{1}{n_m}\sum_{y=1991}^{2020}P_{y,m}
\]

The upper-panel quantity is the precipitation anomaly:

\[
A_{y,m}=P_{y,m}-\overline{P}_{m}^{1991\text{–}2020}
\]

Thus \(A_{y,m}>0\) means a wetter-than-normal month for that specific
calendar month, and \(A_{y,m}<0\) means a drier-than-normal month.

The lower panel is the published Relative Oceanic Niño Index, \(R_s\), in
degrees Celsius, where \(s\) is the centered three-month season. Calendar
months are mapped to seasons as follows:

\[
\text{Jan}\to\text{DJF},\ \text{Feb}\to\text{JFM},\ldots,\ \text{Dec}\to\text{NDJ}
\]

## Data-quality rule

For \(O_{y,m}\) usable daily precipitation values in a month:

\[
\text{coverage}_{y,m}=100\times\frac{O_{y,m}}{D_{y,m}}
\]

The precipitation line is drawn only if:

\[
\text{coverage}_{y,m}\ge90\%
\]

RONI is plotted independently whenever CPC has published the value. Therefore,
RONI remains visible during a local precipitation gap; this distinguishes a
local station-data problem from an ENSO data gap.

## Why the precipitation line has gaps

| Period | Original LCD finding | Figure treatment |
|---|---|---|
| 1995-10 to 1998-03 | No `SOD` daily-summary records or usable `DailyPrecipitation` values | Blank precipitation line |
| 1998-04 | Records begin April 16; 15 of 30 days observed | Blank precipitation line |
| 2000-03 | SOD records exist but all 31 daily precipitation values are blank | Blank precipitation line |

The 1996–1997 source files contain hourly aviation observations, but their
`HourlyPrecipitation` field is blank. Those records cannot reliably replace
the missing daily totals.

## How to read the figure

- Upper dashed line: normal monthly precipitation, \(A_{y,m}=0\).
- Lower dashed line: neutral RONI, \(R_s=0\ \degree\mathrm{C}\).
- Short, high precipitation spikes often reflect individual storms or
  atmospheric rivers. They should not be interpreted as an ENSO effect without
  seasonal analysis.

The latest local month can precede or follow the latest RONI value because the
two NOAA products have different publication schedules.

## Limit

This chart does not test a matched time-scale relationship: precipitation is a
single-month outcome and RONI is a three-month index. The DJF methodology is
the primary matched seasonal analysis.
