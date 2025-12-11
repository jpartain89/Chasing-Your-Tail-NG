# Copilot Coding Agent Instructions

## Repository Overview

**Chasing Your Tail (CYT)** is a Wi-Fi probe request analyzer that monitors and tracks wireless devices. It integrates with Kismet for packet capture and WiGLE API for SSID geolocation analysis, featuring advanced surveillance detection capabilities.

- **Language:** Python 3.6+
- **Target Runtime:** Linux with Wi-Fi monitoring hardware
- **Size:** ~5,000 lines across 15+ Python modules
- **Dependencies:** `requests`, `cryptography` (see `requirements.txt`)

## Build & Validation Commands

### Setup (Always run first)
```bash
pip3 install -r requirements.txt
```
Dependencies are minimal: `requests>=2.28.0` and `cryptography>=40.0.0`. Standard library modules (`sqlite3`, `json`, `tkinter`) are used extensively.

### Validating Module Imports
```bash
python3 -c "from secure_credentials import secure_config_loader; from secure_database import SecureKismetDB; from surveillance_detector import SurveillanceDetector; print('OK')"
```

### Running Components
| Command | Description |
|---------|-------------|
| `python3 chasing_your_tail.py` | Core monitoring (requires Kismet DB) |
| `python3 surveillance_analyzer.py` | Surveillance analysis (requires Kismet DB) |
| `python3 surveillance_analyzer.py --demo` | Demo mode (still requires Kismet DB) |
| `python3 probe_analyzer.py` | Log analysis (requires log files) |
| `python3 probe_analyzer.py --wigle` | Log analysis with WiGLE API |
| `python3 cyt_gui.py` | GUI interface (requires `tkinter`) |

**Expected Behavior Without Data:**
- Without Kismet DB: `FileNotFoundError: No Kismet database found at: ...`
- Without log files: `Error: No log files found! Please check the logs directory`
- These errors are normal in development/CI environments without hardware.

**Note:** `tkinter` may not be available in headless environments. GUI tests should be skipped in CI.

### Environment Variables
- `CYT_TEST_MODE=true` - Enables non-interactive credential handling
- `CYT_MASTER_PASSWORD` - Master password for encrypted credentials (optional)

## Project Architecture

### Core Modules
| File | Purpose |
|------|---------|
| `chasing_your_tail.py` | Main monitoring loop, Kismet DB querying |
| `surveillance_analyzer.py` | GPS-correlated surveillance detection |
| `surveillance_detector.py` | Persistence scoring algorithms |
| `gps_tracker.py` | GPS tracking and KML generation |
| `probe_analyzer.py` | Historical probe data analysis |
| `cyt_gui.py` | Tkinter GUI interface |

### Security Modules
| File | Purpose |
|------|---------|
| `secure_database.py` | Parameterized SQL queries (prevents injection) |
| `secure_credentials.py` | Encrypted credential storage |
| `secure_ignore_loader.py` | Safe ignore list loading (replaces `exec()`) |
| `secure_main_logic.py` | Secure monitoring logic |
| `input_validation.py` | Input sanitization and validation |

### Configuration
- `config.json` - Main configuration (paths, timing, search boundaries)
- `ignore_lists/` - MAC/SSID ignore lists (JSON format preferred)

### Output Directories
- `logs/` - CYT monitoring logs
- `surveillance_reports/` - Generated reports (markdown/HTML)
- `kml_files/` - Google Earth visualization files
- `reports/` - Probe analysis reports
- `analysis_logs/` - Surveillance analysis logs

## Key Implementation Details

### Time Window System
The monitoring system uses four overlapping time windows (5, 10, 15, 20 minutes) to track device persistence. Configuration is in `config.json` under `timing.time_windows`.

### Database Operations
All database queries use `SecureKismetDB` class with parameterized queries. Never construct SQL strings directly. Key tables in Kismet SQLite:
- `devices` - Contains MAC addresses, device types, and JSON device details
- Probe data is in JSON field `device` under `dot11.device.last_probed_ssid_record`

### Ignore List Format
Ignore lists in `ignore_lists/` should be JSON arrays:
```json
["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]
```
The secure loader validates MAC addresses and SSIDs before use.

## Common Issues & Workarounds

1. **No Kismet database found:** The system requires Kismet to be running and logging to a `.kismet` file. Path is configured in `config.json` under `paths.kismet_logs`.

2. **Credential prompts in non-interactive mode:** Set `CYT_TEST_MODE=true` environment variable.

3. **tkinter not available:** GUI components won't work in headless environments. This is expected behavior.

4. **ModuleNotFoundError for cryptography:** Run `pip3 install cryptography>=40.0.0`.

## Validation Checklist

When making changes, verify:
1. Python syntax: `python3 -m py_compile <file.py>`
2. Module imports work: Test with import statements
3. Security modules maintain parameterized queries
4. No hardcoded credentials or API keys
5. Input validation is applied to user inputs

## Files to Never Modify Without Care
- `secure_database.py` - SQL injection prevention
- `secure_credentials.py` - Credential encryption
- `input_validation.py` - Security sanitization

Trust these instructions. Only perform additional searches if information is incomplete or found to be in error.
