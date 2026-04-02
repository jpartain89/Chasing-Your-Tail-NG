"""Tests for unified CYT CLI command routing."""

import sys

import cyt_cli


def test_monitor_command_routes_to_legacy(monkeypatch):
    called = {}

    def fake_run(command):
        called["command"] = command
        return 0

    monkeypatch.setattr(cyt_cli, "_run_legacy", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["cyt_cli.py", "monitor", "--config", "custom.json", "--once"],
    )

    result = cyt_cli.main()
    assert result == 0
    assert called["command"] == ["chasing_your_tail.py", "--config", "custom.json", "--once"]


def test_analyze_command_routes_flags(monkeypatch):
    called = {}

    def fake_probe_runner(use_wigle=False, days_back=14, all_logs=False):
        called["args"] = {
            "use_wigle": use_wigle,
            "days_back": days_back,
            "all_logs": all_logs,
        }
        return 0, "ok\n"

    monkeypatch.setattr(cyt_cli, "run_probe_analysis", fake_probe_runner)
    monkeypatch.setattr(
        sys,
        "argv",
        ["cyt_cli.py", "analyze", "--local", "--days", "7", "--wigle"],
    )

    result = cyt_cli.main()
    assert result == 0
    assert called["args"] == {
        "use_wigle": True,
        "days_back": 7,
        "all_logs": False,
    }


def test_survey_command_routes_optional_args(monkeypatch):
    called = {}

    def fake_surveillance_runner(
        demo=False,
        kismet_db=None,
        gps_file=None,
        stalking_only=False,
        output_json=None,
        min_threat=0.5,
    ):
        called["args"] = {
            "demo": demo,
            "kismet_db": kismet_db,
            "gps_file": gps_file,
            "stalking_only": stalking_only,
            "output_json": output_json,
            "min_threat": min_threat,
        }
        return 0, "ok\n"

    monkeypatch.setattr(cyt_cli, "run_surveillance_analysis", fake_surveillance_runner)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "cyt_cli.py",
            "survey",
            "--demo",
            "--kismet-db",
            "db.sqlite",
            "--min-threat",
            "0.8",
        ],
    )

    result = cyt_cli.main()
    assert result == 0
    assert called["args"] == {
        "demo": True,
        "kismet_db": "db.sqlite",
        "gps_file": None,
        "stalking_only": False,
        "output_json": None,
        "min_threat": 0.8,
    }
