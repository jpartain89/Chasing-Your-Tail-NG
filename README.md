# Chasing Your Tail (CYT)

A comprehensive Wi-Fi probe request analyzer that monitors and tracks wireless devices by analyzing their probe requests. The system integrates with Kismet for packet capture and WiGLE API for SSID geolocation analysis, featuring advanced surveillance detection capabilities.

## 🚨 Security Notice

This project has been security-hardened to eliminate critical vulnerabilities:
- **SQL injection prevention** with parameterized queries
- **Encrypted credential management** for API keys
- **Input validation** and sanitization
- **Secure ignore list loading** (no more `exec()` calls)

## Features

- **Real-time Wi-Fi monitoring** with Kismet integration
- **Advanced surveillance detection** with persistence scoring
- **🆕 Unified Installation** - Single install script for all dependencies
- **🆕 Setup Wizard** - Guided configuration on first run
- **🆕 Touch-Friendly GUI** - Optimized for small screens and touch interfaces
- **Automatic GPS integration** - extracts coordinates from Bluetooth GPS via Kismet
- **GPS correlation** and location clustering (100m threshold)
- **Spectacular KML visualization** for Google Earth with professional styling
- **Multi-format reporting** - Markdown, HTML (with pandoc), and KML outputs
- **Time-window tracking** (5, 10, 15, 20 minute windows)
- **WiGLE API integration** for SSID geolocation
- **Multi-location tracking algorithms** for detecting following behavior
- **Enhanced GUI interface** with surveillance analysis button
- **Organized file structure** with dedicated output directories

## Requirements

- Python 3.6+
- Kismet wireless packet capture
- Wi-Fi adapter supporting monitor mode
- Linux-based system
- WiGLE API key (optional)

## Quick Installation

### One-Line Install
```bash
# Make the script executable (first time only)
chmod +x install.sh

# Run the installer
./install.sh

# Alternative: run with bash directly (no chmod needed)
bash install.sh
```

This will install all system dependencies, Python packages, and set up the required directories.

### Manual Installation

#### 1. Install System Dependencies
```bash
sudo apt-get install python3 python3-pip python3-tk wireless-tools iw pandoc gpsd
```

#### 2. Install Python Dependencies
```bash
pip3 install -r requirements.txt
```

#### 3. Run Setup Wizard
```bash
python3 setup_wizard.py
```
Or the setup wizard will run automatically on first GUI launch.

## Usage

### Unified CLI (Recommended for automation)
```bash
# Show all commands
python3 cyt_cli.py --help

# Monitor (single cycle)
python3 cyt_cli.py monitor --once

# Probe analysis (local only)
python3 cyt_cli.py analyze --days 14

# Surveillance analysis (demo data)
python3 cyt_cli.py survey --demo

# Setup wizard
python3 cyt_cli.py setup --cli
```

### GUI Interface (Recommended)
```bash
python3 cyt_gui.py
```
**GUI Features:**
- 🚀 **Start CYT** - Begin real-time Wi-Fi monitoring
- 🗺️ **Surveillance Analysis** - GPS-correlated persistence detection with KML visualization
- 📈 **Analyze Logs** - Historical probe request analysis
- ⚙️ **Settings** - Configure paths, intervals, and run setup wizard
- 📝 **Create/Delete Ignore Lists** - Manage MAC/SSID filtering
- Real-time status monitoring and file generation notifications

### Command Line Monitoring
```bash
# Start core monitoring (secure)
python3 chasing_your_tail.py --once

# Start Kismet (ONLY working script - July 23, 2025 fix)
./start_kismet_clean.sh
```

### Data Analysis
```bash
# Analyze collected probe data (past 14 days, local only - default)
python3 probe_analyzer.py

# Analyze past 7 days only
python3 probe_analyzer.py --days 7

# Analyze ALL logs (may be slow for large datasets)
python3 probe_analyzer.py --all-logs

# Analyze WITH WiGLE API calls (consumes API credits!)
python3 probe_analyzer.py --wigle
```

### Surveillance Detection & Advanced Visualization
```bash
# 🆕 NEW: Automatic GPS extraction with spectacular KML visualization
python3 surveillance_analyzer.py

# Run analysis with demo GPS data (for testing - uses Phoenix coordinates)
python3 surveillance_analyzer.py --demo

# Analyze specific Kismet database
python3 surveillance_analyzer.py --kismet-db /path/to/kismet.db

# Focus on stalking detection with high persistence threshold
python3 surveillance_analyzer.py --stalking-only --min-persistence 0.8

# Export results to JSON for further analysis
python3 surveillance_analyzer.py --output-json analysis_results.json

# Analyze with external GPS data from JSON file
python3 surveillance_analyzer.py --gps-file gps_coordinates.json
```

### Ignore List Management
```bash
# Create new ignore lists from current Kismet data
python3 legacy/create_ignore_list.py  # Moved to legacy folder
```
**Note**: Ignore lists are now stored as JSON files in `./ignore_lists/`

## Core Components

- **chasing_your_tail.py**: Core monitoring engine with real-time Kismet database queries
- **cyt_gui.py**: Enhanced Tkinter GUI with surveillance analysis capabilities
- **surveillance_analyzer.py**: GPS surveillance detection with automatic coordinate extraction and advanced KML visualization
- **surveillance_detector.py**: Core persistence detection engine for suspicious device patterns
- **gps_tracker.py**: GPS tracking with location clustering and spectacular Google Earth KML generation
- **probe_analyzer.py**: Post-processing tool with WiGLE integration
- **start_kismet_clean.sh**: ONLY working Kismet startup script (July 23, 2025 fix)

### Security Components
- **secure_database.py**: SQL injection prevention
- **secure_credentials.py**: Encrypted credential management
- **secure_ignore_loader.py**: Safe ignore list loading
- **secure_main_logic.py**: Secure monitoring logic
- **input_validation.py**: Input sanitization and validation
- **legacy/migrate_credentials.py**: Legacy one-time credential migration helper

## Output Files & Project Structure

### Organized Output Directories
- **Surveillance Reports**: `./surveillance_reports/surveillance_report_YYYYMMDD_HHMMSS.md` (markdown)
- **HTML Reports**: `./surveillance_reports/surveillance_report_YYYYMMDD_HHMMSS.html` (styled HTML with pandoc)
- **KML Visualizations**: `./kml_files/surveillance_analysis_YYYYMMDD_HHMMSS.kml` (spectacular Google Earth files)
- **CYT Logs**: `./logs/cyt_log_MMDDYY_HHMMSS`
- **Analysis Logs**: `./analysis_logs/surveillance_analysis.log`
- **Probe Reports**: `./reports/probe_analysis_report_YYYYMMDD_HHMMSS.txt`

### Configuration & Data
- **Ignore Lists**: `./ignore_lists/mac_list.json`, `./ignore_lists/ssid_list.json`
- **Encrypted Credentials**: `./secure_credentials/encrypted_credentials.json`

### Archive Directories (Cleaned July 23, 2025)
- **old_scripts/**: All broken startup scripts with hanging pkill commands
- **docs_archive/**: Session notes, old configs, backup files, duplicate logs
- **legacy/**: Original legacy code archive (pre-security hardening)

## Technical Architecture

### Time Window System
Maintains four overlapping time windows to detect device persistence:
- Recent: Past 5 minutes
- Medium: 5-10 minutes ago
- Old: 10-15 minutes ago
- Oldest: 15-20 minutes ago

### Surveillance Detection
Advanced persistence detection algorithms analyze device behavior patterns:
- **Temporal Persistence**: Consistent device appearances over time
- **Location Correlation**: Devices following across multiple locations
- **Probe Pattern Analysis**: Suspicious SSID probe requests
- **Timing Analysis**: Unusual appearance patterns
- **Persistence Scoring**: Weighted scores (0-1.0) based on combined indicators
- **Multi-location Tracking**: Specialized algorithms for detecting following behavior

### GPS Integration & Spectacular KML Visualization (Enhanced!)
- **🆕 Automatic GPS extraction** from Kismet database (Bluetooth GPS support)
- **Location clustering** with 100m threshold for grouping nearby coordinates
- **Session management** with timeout handling for location transitions
- **Device-to-location correlation** links Wi-Fi devices to GPS positions
- **Professional KML generation** with spectacular Google Earth visualizations featuring:
  - Color-coded persistence level markers (green/yellow/red)
  - Device tracking paths showing movement correlation
  - Rich interactive balloon content with detailed device intelligence
  - Activity heatmaps and surveillance intensity zones
  - Temporal analysis overlays for time-based pattern detection
- **Multi-location tracking** detects devices following across locations with visual tracking paths

## Configuration

All settings are centralized in `config.json`:
```json
{
  "paths": {
    "base_dir": ".",
    "log_dir": "logs",
    "reports_dir": "reports",
    "kml_dir": "kml_files",
    "surveillance_reports_dir": "surveillance_reports",
    "analysis_logs_dir": "analysis_logs",
    "kismet_logs": "/home/matt/kismet_logs/*.kismet",
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

WiGLE API credentials are now securely encrypted in `secure_credentials/encrypted_credentials.json`.

## Testing

This project includes a comprehensive test suite with automated CI/CD via GitHub Actions.

### Running Tests Locally

```bash
# Install test dependencies
pip3 install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_setup_wizard.py -v
```

### Test Coverage

The test suite includes:
- **Unit tests** for setup wizard, input validation, and security modules
- **Integration tests** for installation scripts and module imports
- **Coverage reporting** to track code coverage
- **Automated CI/CD** that runs on every pull request

Tests run automatically on PRs against Python 3.8, 3.9, 3.10, 3.11, and 3.12.

See `tests/README.md` for more details on the test suite.

## Migration Notes

- Legacy one-off scripts were moved from project root to `legacy/`:
  - `legacy/blackhat_demo.py`
  - `legacy/create_ignore_list.py`
  - `legacy/ignore_list.py`
  - `legacy/ignore_list_ssid.py`
  - `legacy/migrate_credentials.py`
- Root-level workflows should use `cyt_cli.py`, `chasing_your_tail.py`, `probe_analyzer.py`, `surveillance_analyzer.py`, and `setup_wizard.py`.
- Startup automation should use only `start_kismet_clean.sh` and `start_gui.sh`.

## Deprecation Timeline

- Current cycle:
  - Soft compatibility is preserved (legacy entry points still work where wrappers exist).
  - New automation and docs target `cyt_cli.py`.
- Next release cycle:
  - Legacy script usage is supported but treated as maintenance-only.
  - No new features will be added to files under `legacy/`.
- Future major cleanup:
  - Legacy scripts under `legacy/` may be removed after adoption of the unified CLI path.

## Manual Validation Checklist

Run these before release:

```bash
export CYT_TEST_MODE=true
python3 cyt_cli.py --help
python3 cyt_cli.py monitor --help
python3 cyt_cli.py analyze --help
python3 cyt_cli.py survey --help
python3 cyt_cli.py setup --help
python3 chasing_your_tail.py --once
python3 probe_analyzer.py --days 1
python3 surveillance_analyzer.py --demo
python3 -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing --cov-report=xml
python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv,legacy
```

## Security Features

- **Parameterized SQL queries** prevent injection attacks
- **Encrypted credential storage** protects API keys
- **Input validation** prevents malicious input
- **Audit logging** tracks all security events
- **Safe ignore list loading** eliminates code execution risks

## Author

@matt0177

## License

MIT License

## Disclaimer

This tool is intended for legitimate security research, network administration, and personal safety purposes. Users are responsible for complying with all applicable laws and regulations in their jurisdiction.