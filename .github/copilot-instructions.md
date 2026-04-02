# Copilot Coding Agent Instructions

## Repository Summary

**Chasing Your Tail (CYT)** is a Python-based Wi-Fi probe request analyzer for detecting physical surveillance. It monitors wireless devices via Kismet integration, performs GPS-correlated persistence detection, and generates KML visualizations for Google Earth. This is a fork of ArgeliusLabs/Chasing-Your-Tail-NG.

- **Language:** Python (~279K lines) with Shell scripts (~15K lines)
- **Runtime:** Python 3.8–3.12 (CI-tested); Linux target with Wi-Fi monitoring hardware
- **Dependencies:** `requests>=2.28.0`, `cryptography>=40.0.0`, `pytest>=7.0.0`, `pytest-cov>=4.0.0`
- **License:** MIT

## Build & Validation — Exact Commands

### 1. Install Dependencies (always run first)
```bash
pip install -r requirements.txt
```

### 2. Run Tests
```bash
pytest tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=xml
```
This is the exact command the CI workflow uses. The `pytest.ini` already configures verbose output, strict markers, short tracebacks, and coverage reporting (HTML, XML, term-missing) — running bare `pytest` also works but the above matches CI exactly.

**Test files:**
- `tests/test_setup_wizard.py` — SetupConfig, CLISetupWizard, needs_setup
- `tests/test_input_validation.py` — MAC/SSID/path validation, string sanitization, config structure
- `tests/test_integration.py` — install.sh script verification, Python module imports, requirements.txt checks

### 3. Validate Syntax of Changed Files
```bash
python3 -m py_compile <file.py>
```

### 4. Validate Module Imports
```bash
python3 -c "from secure_credentials import secure_config_loader; from secure_database import SecureKismetDB; from surveillance_detector import SurveillanceDetector; from input_validation import InputValidator; from setup_wizard import SetupConfig; print('OK')"
```

### 5. Lint (CI runs these with `continue-on-error: true`, so they are non-blocking)
```bash
# Fatal errors only (syntax errors, undefined names) — this DOES fail the build if errors found
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
# All warnings (non-blocking)
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## CI Workflow (`.github/workflows/python-tests.yml`)

Triggered on push/PR to `main`, `master`, `develop` branches when `**.py`, `requirements.txt`, `tests/**`, or the workflow file changes. Three jobs:

| Job | Blocking? | What it does |
|-----|-----------|-------------|
| **test** | ✅ Yes | Runs `pytest` across Python 3.8, 3.9, 3.10, 3.11, 3.12 on ubuntu-latest |
| **lint** | ❌ No (`continue-on-error`) | Runs `black --check`, `flake8` |
| **security** | ❌ No (`continue-on-error`) | Runs `bandit`, `safety check` |

**Only the `test` job can fail the PR.** Always ensure `pytest` passes before submitting.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `CYT_TEST_MODE=true` | **Required in CI/headless.** Prevents interactive password prompts in `secure_credentials.py` (uses `test_password_123` fallback). |
| `CYT_MASTER_PASSWORD` | Optional master password for credential encryption. |

## Project Layout

### Root Files
| File | Purpose |
|------|---------|
| `chasing_your_tail.py` | **Entry point** — main monitoring loop, queries Kismet SQLite DB |
| `cyt_gui.py` | Tkinter GUI (requires display; skip in headless/CI) |
| `surveillance_analyzer.py` | GPS-correlated surveillance detection orchestrator |
| `surveillance_detector.py` | Core persistence scoring algorithms (largest file, ~47KB) |
| `gps_tracker.py` | GPS tracking + KML generation (~41KB) |
| `probe_analyzer.py` | Post-processing historical probe data with WiGLE |
| `setup_wizard.py` | First-run configuration wizard (~35KB) |
| `config.json` | Central configuration: paths, timing windows, search boundaries |
| `requirements.txt` | Python dependencies |
| `pytest.ini` | Pytest configuration (test paths, markers, coverage settings) |
| `.coveragerc` | Coverage configuration (source=`.`, omits tests/venv/etc.) |
| `install.sh` | System-level installer (supports `--help`, `--verify` flags) |
| `blackhat_demo.py` | Demo script for presentations |

### Security Modules (modify with extreme care)
| File | Purpose |
|------|---------|
| `secure_database.py` | `SecureKismetDB` — parameterized SQL queries |
| `secure_credentials.py` | `SecureCredentialManager` — Fernet encryption for API keys |
| `secure_ignore_loader.py` | Safe ignore list loading (replaced dangerous `exec()`) |
| `secure_main_logic.py` | `SecureCYTMonitor` — secure monitoring logic |
| `input_validation.py` | `InputValidator` — MAC, SSID, path, config validation |
| `migrate_credentials.py` | One-time credential migration tool |

### Directories
| Path | Purpose |
|------|---------|
| `tests/` | Pytest test suite (3 test files + `__init__.py` + `README.md`) |
| `.github/workflows/` | CI workflow (`python-tests.yml`) |
| `ignore_lists/` | JSON MAC/SSID ignore lists (gitignored at runtime) |
| `logs/`, `reports/`, `kml_files/`, `surveillance_reports/`, `analysis_logs/` | Output directories (all gitignored) |
| `secure_credentials/` | Encrypted credential storage (gitignored) |

### Configuration (`config.json`)
```json
{
  "paths": { "base_dir": ".", "log_dir": "logs", "kismet_logs": "...", "ignore_lists": { "mac": "mac_list.json", "ssid": "ssid_list.json" } },
  "timing": { "check_interval": 60, "list_update_interval": 5, "time_windows": { "recent": 5, "medium": 10, "old": 15, "oldest": 20 } },
  "search": { "lat_min": 31.3, "lat_max": 37.0, "lon_min": -114.8, "lon_max": -109.0 }
}
```

## Key Constraints & Rules

1. **Never construct raw SQL strings.** Always use `SecureKismetDB` with parameterized queries.
2. **Never hardcode credentials or API keys.** Use `SecureCredentialManager`.
3. **All user input must pass through `InputValidator`** methods before use.
4. **Ignore lists must be JSON arrays**, e.g., `["AA:BB:CC:DD:EE:FF"]`. The secure loader (`secure_ignore_loader.py`) validates entries.
5. **New tests** go in `tests/` as `test_*.py`. Use `pytest.mark.unit`, `pytest.mark.integration`, or `pytest.mark.slow` markers.
6. **GUI code (`cyt_gui.py`)** depends on `tkinter` which is unavailable in headless/CI environments — tests should not import it directly.
7. Shell scripts (`install.sh`, `start_kismet_clean.sh`, etc.) target Linux and may reference `/home/matt/` paths.

## Common Errors & Workarounds

| Error | Cause | Fix |
|-------|-------|-----|
| `FileNotFoundError: No Kismet database found` | No `.kismet` file at configured path | Normal in dev/CI — no hardware needed for tests |
| Interactive password prompt hangs | `secure_credentials.py` prompts for master password | Set `CYT_TEST_MODE=true` environment variable |
| `ModuleNotFoundError: No module named 'tkinter'` | Headless environment | Expected — do not test GUI directly in CI |
| `ModuleNotFoundError: No module named 'cryptography'` | Missing dependency | Run `pip install -r requirements.txt` |

## Trust These Instructions

Use this document as the authoritative reference for building, testing, and validating changes. Only perform additional repository exploration if the information here is incomplete or found to be incorrect.