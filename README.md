# econCalScraper

Scrapes the [FXStreet economic calendar](https://www.fxstreet.com/economic-calendar)
and saves the results as CSVs, organized by year and month.

## How it works

The FXStreet calendar page is powered by a public JSON API
(`calendar-api.fxstreet.com`) that the site's own widget calls in the
browser — no API key or authentication required. `scrape_calendar.py` calls
that API once per month for a given year and writes the results to CSV.

## Usage

Requires Python 3 and the `requests` package (`pip install requests`).

```
python scrape_calendar.py [year] [--out-dir data] [--delay 1.5]
```

- `year` — defaults to the current year if omitted.
- `--out-dir` — base directory for output (default `data`).
- `--delay` — seconds to wait between monthly requests (default `1.5`).

Output is written to `<out-dir>/<year>/<year>-<month>.csv`, e.g.
`data/2026/2026-01.csv`.

## CSV columns

| Column | Description |
| --- | --- |
| `date_utc` | Event date (UTC) |
| `time_utc` | Event time (UTC), blank for all-day events |
| `country` | Country code (e.g. `US`, `EMU`) |
| `currency` | Currency code (e.g. `USD`, `EUR`) |
| `category` | Event category (e.g. Labor Market, Inflation) |
| `event` | Event name |
| `importance` | Volatility/impact rating: `NONE`, `LOW`, `MEDIUM`, `HIGH` |
| `actual` | Actual reported value |
| `consensus` | Forecast/consensus value |
| `previous` | Previous period's value |
| `revised` | Revised previous value, if any |
| `unit` | Unit of the value (e.g. `%`, `$`) |
| `potency` | Magnitude of the value (e.g. `K`, `M`, `B`) |
| `is_all_day` | Whether the event is an all-day entry (e.g. holidays) |
| `is_tentative` | Whether the event date/time is tentative |
| `is_preliminary` | Whether the actual value is preliminary |
| `is_report` | Whether the event is a report release |
| `is_speech` | Whether the event is a speech |
| `event_id` | FXStreet's internal event identifier |

Events for dates in the future naturally have empty `actual` values since
they haven't occurred yet.

## Data directory

`data/` is git-ignored since it's fully regenerable by re-running the
script — it currently holds monthly CSVs for 2010–2026.
