# CYT Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 2. Configure Secure Runtime
```bash
export CYT_TEST_MODE=true  # use only for non-interactive testing/CI
```

For legacy credential migration helpers, use:
```bash
python3 legacy/migrate_credentials.py
```

### 3. Verify Configuration
Ensure `config.json` uses the current schema:

```json
{
  "paths": {
    "base_dir": ".",
    "log_dir": "logs",
    "reports_dir": "reports",
    "kml_dir": "kml_files",
    "surveillance_reports_dir": "surveillance_reports",
    "analysis_logs_dir": "analysis_logs",
    "kismet_logs": "/home/*/kismet_logs/*.kismet",
    "ignore_lists": {
      "mac": "mac_list.json",
      "ssid": "ssid_list.json"
    }
  },
  "timing": {
    "check_interval": 60,
    "list_update_interval": 5,
    "time_windows": {
      "recent": 5,
      "medium": 10,
      "old": 15,
      "oldest": 20
    }
  }
}
```

## Run Modes

### Unified CLI (preferred)
```bash
python3 cyt_cli.py --help
python3 cyt_cli.py monitor --once
python3 cyt_cli.py analyze --days 14
python3 cyt_cli.py survey --demo
python3 cyt_cli.py setup --cli
```

### GUI
```bash
python3 cyt_gui.py
```

### Direct scripts (supported)
```bash
python3 chasing_your_tail.py --once
python3 probe_analyzer.py --days 7
python3 surveillance_analyzer.py --demo
python3 setup_wizard.py --cli
```

## Startup Scripts (authoritative)

Use only these scripts for startup automation:

```bash
./start_kismet_clean.sh
./start_gui.sh
```

## Output Locations

- `logs/` real-time CYT logs
- `reports/` probe analysis text reports
- `surveillance_reports/` markdown/html surveillance reports
- `kml_files/` generated KML visualizations
- `analysis_logs/` surveillance analyzer logs

## Verification Commands

```bash
export CYT_TEST_MODE=true
python3 -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=xml
python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv,legacy
```

## Notes

- `legacy/` contains archived one-off scripts retained for reference.
- New feature work should target shared runtime services and `cyt_cli.py`.
