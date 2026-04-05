"""Tests for cyt_core_runtime.py — RuntimeContext, MonitoringService, BackgroundMonitoringRunner."""

import glob as glob_module
import json
import os
import sys
import threading
import time

import pytest

os.environ["CYT_TEST_MODE"] = "true"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cyt_core_runtime as rt
from cyt_core_runtime import (
    BackgroundMonitoringRunner,
    MonitoringService,
    RuntimeContext,
    discover_latest_kismet_db,
    ensure_runtime_directories,
    load_runtime_context,
)
from secure_credentials import SecureCredentialManager

# ---------------------------------------------------------------------------
# Minimal config helpers
# ---------------------------------------------------------------------------

MINIMAL_CONFIG = {
    "paths": {
        "base_dir": ".",
        "log_dir": "logs",
        "kismet_logs": "/nonexistent/*.kismet",
        "ignore_lists": {"mac": "mac_list.json", "ssid": "ssid_list.json"},
    },
    "timing": {"check_interval": 60, "list_update_interval": 5},
}


def _write_config(path, cfg=None):
    cfg = cfg or MINIMAL_CONFIG
    with open(path, "w") as f:
        json.dump(cfg, f)


# ---------------------------------------------------------------------------
# RuntimeContext
# ---------------------------------------------------------------------------


class TestRuntimeContext:

    @pytest.mark.unit
    def test_dataclass_holds_config_and_cred_manager(self):
        mgr = SecureCredentialManager.__new__(SecureCredentialManager)
        ctx = RuntimeContext(config={"key": "value"}, credential_manager=mgr)
        assert ctx.config["key"] == "value"
        assert ctx.credential_manager is mgr


# ---------------------------------------------------------------------------
# load_runtime_context
# ---------------------------------------------------------------------------


class TestLoadRuntimeContext:

    @pytest.mark.unit
    def test_returns_runtime_context(self, tmp_path, monkeypatch):
        config_file = str(tmp_path / "config.json")
        cfg = dict(MINIMAL_CONFIG)
        cfg["paths"] = dict(MINIMAL_CONFIG["paths"])
        cfg["paths"]["log_dir"] = str(tmp_path / "logs")
        _write_config(config_file, cfg)

        ctx = load_runtime_context(config_file)
        assert isinstance(ctx, RuntimeContext)
        assert "paths" in ctx.config
        assert isinstance(ctx.credential_manager, SecureCredentialManager)

    @pytest.mark.unit
    def test_raises_on_missing_config(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_runtime_context(str(tmp_path / "missing.json"))


# ---------------------------------------------------------------------------
# ensure_runtime_directories
# ---------------------------------------------------------------------------


class TestEnsureRuntimeDirectories:

    @pytest.mark.unit
    def test_creates_log_dir(self, tmp_path):
        log_dir = tmp_path / "newlogs"
        assert not log_dir.exists()
        cfg = {"paths": {"log_dir": str(log_dir)}}
        ensure_runtime_directories(cfg)
        assert log_dir.exists()

    @pytest.mark.unit
    def test_idempotent_when_dir_exists(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        cfg = {"paths": {"log_dir": str(log_dir)}}
        ensure_runtime_directories(cfg)  # Should not raise
        assert log_dir.exists()

    @pytest.mark.unit
    def test_creates_all_output_dirs(self, tmp_path):
        cfg = {
            "paths": {
                "log_dir": str(tmp_path / "logs"),
                "reports_dir": str(tmp_path / "reports"),
                "kml_dir": str(tmp_path / "kml_files"),
                "surveillance_reports_dir": str(tmp_path / "surveillance_reports"),
                "analysis_logs_dir": str(tmp_path / "analysis_logs"),
            }
        }
        ensure_runtime_directories(cfg)
        for key, value in cfg["paths"].items():
            assert os.path.isdir(value), f"{key} dir not created: {value}"

    @pytest.mark.unit
    def test_missing_optional_keys_skipped(self, tmp_path):
        cfg = {"paths": {"log_dir": str(tmp_path / "logs")}}
        ensure_runtime_directories(cfg)  # Should not raise
        assert (tmp_path / "logs").exists()


# ---------------------------------------------------------------------------
# discover_latest_kismet_db
# ---------------------------------------------------------------------------


class TestDiscoverLatestKismetDB:

    @pytest.mark.unit
    def test_raises_when_no_files_match(self):
        with pytest.raises(FileNotFoundError):
            discover_latest_kismet_db("/nonexistent/path/*.kismet")

    @pytest.mark.unit
    def test_returns_newest_file(self, tmp_path, monkeypatch):
        old_file = tmp_path / "old.kismet"
        new_file = tmp_path / "new.kismet"
        old_file.write_text("old")
        time.sleep(0.01)
        new_file.write_text("new")

        result = discover_latest_kismet_db(str(tmp_path / "*.kismet"))
        assert result == str(new_file)

    @pytest.mark.unit
    def test_single_file_in_glob(self, tmp_path):
        only_file = tmp_path / "only.kismet"
        only_file.write_text("data")
        result = discover_latest_kismet_db(str(tmp_path / "*.kismet"))
        assert result == str(only_file)


# ---------------------------------------------------------------------------
# MonitoringService (with mocks)
# ---------------------------------------------------------------------------


class TestMonitoringServiceInitialize:

    @pytest.mark.unit
    def test_initialize_discovers_db_and_validates(self, tmp_path, monkeypatch):
        """MonitoringService.initialize should call SecureKismetDB.validate_connection."""
        import cyt_core_runtime as rt_mod

        cfg = dict(MINIMAL_CONFIG)
        cfg["paths"] = dict(MINIMAL_CONFIG["paths"])
        cfg["paths"]["log_dir"] = str(tmp_path / "logs")
        cfg["paths"]["kismet_logs"] = str(tmp_path / "*.kismet")

        (tmp_path / "test.kismet").write_text("db")

        mgr = SecureCredentialManager.__new__(SecureCredentialManager)
        ctx = RuntimeContext(config=cfg, credential_manager=mgr)
        log_file = tmp_path / "test.log"

        db_validated = {}

        class FakeDB:
            def __init__(self, path):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def validate_connection(self):
                db_validated["called"] = True
                return True

        class FakeMonitor:
            def __init__(self, config, ignore, probe_ignore, log_file):
                pass

            def initialize_tracking_lists(self, db):
                pass

        monkeypatch.setattr(rt_mod, "SecureKismetDB", FakeDB)
        monkeypatch.setattr(rt_mod, "SecureCYTMonitor", FakeMonitor)
        monkeypatch.setattr(rt_mod, "load_ignore_lists", lambda _: ([], []))

        with open(str(log_file), "w") as lf:
            service = MonitoringService(ctx, lf)
            result = service.initialize()

        assert db_validated.get("called") is True
        assert result.endswith(".kismet")

    @pytest.mark.unit
    def test_initialize_raises_on_db_validation_failure(self, tmp_path, monkeypatch):
        import cyt_core_runtime as rt_mod

        cfg = dict(MINIMAL_CONFIG)
        cfg["paths"] = dict(MINIMAL_CONFIG["paths"])
        cfg["paths"]["log_dir"] = str(tmp_path / "logs")
        cfg["paths"]["kismet_logs"] = str(tmp_path / "*.kismet")

        (tmp_path / "test.kismet").write_text("db")

        mgr = SecureCredentialManager.__new__(SecureCredentialManager)
        ctx = RuntimeContext(config=cfg, credential_manager=mgr)

        class FakeDB:
            def __init__(self, path):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def validate_connection(self):
                return False  # Simulate failure

        class FakeMonitor:
            def __init__(self, *args, **kwargs):
                pass

            def initialize_tracking_lists(self, db):
                pass

        monkeypatch.setattr(rt_mod, "SecureKismetDB", FakeDB)
        monkeypatch.setattr(rt_mod, "SecureCYTMonitor", FakeMonitor)
        monkeypatch.setattr(rt_mod, "load_ignore_lists", lambda _: ([], []))

        log_file = tmp_path / "test.log"
        with open(str(log_file), "w") as lf:
            service = MonitoringService(ctx, lf)
            with pytest.raises(RuntimeError, match="validation failed"):
                service.initialize()

    @pytest.mark.unit
    def test_run_cycle_raises_when_not_initialized(self, tmp_path):
        mgr = SecureCredentialManager.__new__(SecureCredentialManager)
        ctx = RuntimeContext(config=MINIMAL_CONFIG, credential_manager=mgr)
        log_file = tmp_path / "test.log"
        with open(str(log_file), "w") as lf:
            service = MonitoringService(ctx, lf)
            with pytest.raises(RuntimeError, match="must be initialized"):
                service.run_cycle(1)


# ---------------------------------------------------------------------------
# BackgroundMonitoringRunner — lifecycle
# ---------------------------------------------------------------------------


class TestBackgroundMonitoringRunner:

    @pytest.mark.unit
    def test_stop_sets_stop_event(self):
        runner = BackgroundMonitoringRunner(config_path="config.json")
        assert not runner._stop_event.is_set()
        runner.stop()
        assert runner._stop_event.is_set()

    @pytest.mark.unit
    def test_terminate_is_alias_for_stop(self):
        runner = BackgroundMonitoringRunner(config_path="config.json")
        runner.terminate()
        assert runner._stop_event.is_set()

    @pytest.mark.unit
    def test_terminate_can_be_called_multiple_times(self):
        runner = BackgroundMonitoringRunner(config_path="config.json")
        runner.terminate()
        runner.terminate()  # Should not raise
        assert runner._stop_event.is_set()

    @pytest.mark.unit
    def test_on_output_callback_invoked(self, tmp_path, monkeypatch):
        """Run emits messages through the on_output callback before stop."""
        import cyt_core_runtime as rt_mod

        cfg = dict(MINIMAL_CONFIG)
        cfg["paths"] = dict(MINIMAL_CONFIG["paths"])
        cfg["paths"]["log_dir"] = str(tmp_path / "logs")
        cfg["paths"]["kismet_logs"] = str(tmp_path / "*.kismet")

        (tmp_path / "test.kismet").write_text("db")
        (tmp_path / "logs").mkdir(parents=True, exist_ok=True)

        class FakeDB:
            def __init__(self, path):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def validate_connection(self):
                return True

        class FakeMonitor:
            def __init__(self, *args, **kwargs):
                pass

            def initialize_tracking_lists(self, db):
                pass

            def process_current_activity(self, db):
                pass

            def rotate_tracking_lists(self, db):
                pass

        monkeypatch.setattr(rt_mod, "SecureKismetDB", FakeDB)
        monkeypatch.setattr(rt_mod, "SecureCYTMonitor", FakeMonitor)
        monkeypatch.setattr(rt_mod, "load_ignore_lists", lambda _: ([], []))

        captured = []

        config_file = str(tmp_path / "config.json")
        _write_config(config_file, cfg)

        runner = BackgroundMonitoringRunner(
            config_path=config_file,
            on_output=lambda msg: captured.append(msg),
        )
        # Stop immediately after starting so the loop exits quickly.
        runner.stop()
        return_code = runner.run()

        assert return_code == 0
        assert any("Current Time" in m for m in captured)
