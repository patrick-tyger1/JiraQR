# JiraQR

Raspberry Pi kiosk app for scanning serial numbers and checking latest QC results.

## Behavior

When a serial number is scanned (scanner as keyboard + Enter):

- If no result files are found for the serial: full-screen red message `No Results Found` until touch/click.
- If the latest result file for the serial is `FAILED`: full-screen red message `Latest Result Found - Failure` until touch/click.
- If the latest result file for the serial is `PASSED`: full-screen green `PASS` for 1 second, then return to ready state.

## Result file naming

The app scans a folder of files where each file represents one QC test run.

Supported filename patterns include:

- `YYYYMMDDTHHMMSSZ_PASSED_<serial>.txt`
- `YYYYMMDDTHHMMSSZ_FAILED_<serial>.txt`
- `PASSED_<serial>.txt` / `FAILED_<serial>.txt` (falls back to file modified time for latest ordering)

## Run from terminal

```bash
python3 app.py --results-dir ./sample_data
```

Press `Esc` to exit.

## Run from a desktop icon (recommended)

Install a clickable launcher icon and app entry:

```bash
./scripts/install_desktop_icon.sh
```

This creates:

- `~/Desktop/jiraqr.desktop`
- `~/.local/share/applications/jiraqr.desktop`

Then launch **JiraQR QC Scanner** from desktop/menu. If your desktop asks, trust/allow launching for the icon.

The launcher uses `scripts/run_jiraqr.sh`, which supports optional env vars:

- `JIRAQR_RESULTS_DIR` (default: `./sample_data`)
- `JIRAQR_PASS_DURATION_MS` (default: `1000`)

## Tests

```bash
pytest
```

## Sample data

See `sample_data/` for local validation files.
