"""Tests for direct analysis runner functions."""

import os

os.environ["CYT_TEST_MODE"] = "true"

import probe_analyzer
import surveillance_analyzer


def test_run_probe_analysis_no_logs(monkeypatch):
    monkeypatch.setattr(probe_analyzer.glob, "glob", lambda _pattern: [])

    code, output = probe_analyzer.run_probe_analysis(use_wigle=False, days_back=14, all_logs=False)
    assert code == 1
    assert "No log files found" in output


def test_run_probe_analysis_success_with_stub(monkeypatch):
    monkeypatch.setattr(probe_analyzer.glob, "glob", lambda _pattern: ["logs/cyt_log_010126_010101"])

    class FakeProbeAnalyzer:
        def __init__(self, local_only=True, days_back=14):
            self.local_only = local_only
            self.days_back = days_back

        def parse_all_logs(self):
            return None

        def analyze_probes(self):
            return [
                {
                    "ssid": "TestSSID",
                    "count": 2,
                    "first_seen": "01-01-26 00:00:00",
                    "last_seen": "01-01-26 00:05:00",
                    "wigle_data": None,
                }
            ]

    monkeypatch.setattr(probe_analyzer, "ProbeAnalyzer", FakeProbeAnalyzer)

    code, output = probe_analyzer.run_probe_analysis(use_wigle=False, days_back=7, all_logs=False)
    assert code == 0
    assert "Found 1 unique SSIDs" in output
    assert "SSID: TestSSID" in output


def test_run_surveillance_analysis_success_with_stub(monkeypatch):
    class FakeSurveillanceAnalyzer:
        def __init__(self):
            self.called = False

        def generate_demo_analysis(self):
            self.called = True
            return {"ok": True}

        def analyze_kismet_data(self, kismet_db_path=None, gps_data=None):
            self.called = True
            return {"ok": True}

        def analyze_for_stalking(self, min_persistence_score=0.5):
            return []

        def export_results_json(self, results, output_file):
            return None

    monkeypatch.setattr(surveillance_analyzer, "SurveillanceAnalyzer", FakeSurveillanceAnalyzer)

    code, output = surveillance_analyzer.run_surveillance_analysis(demo=True)
    assert code == 0
    assert "Analysis complete" in output
