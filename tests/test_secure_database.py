"""Tests for secure_database.py — SecureKismetDB and SecureTimeWindows."""

import json
import sqlite3
import sys
import time
import os
from typing import List, Optional

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_database import SecureKismetDB, SecureTimeWindows, create_secure_db_connection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_device_json(ssid: Optional[str] = None) -> str:
    """Build minimal Kismet device JSON with optional probe SSID."""
    doc: dict = {}
    if ssid is not None:
        doc = {
            "dot11.device": {
                "dot11.device.last_probed_ssid_record": {
                    "dot11.probedssid.ssid": ssid,
                }
            }
        }
    return json.dumps(doc)


@pytest.fixture()
def mem_db(tmp_path):
    """An in-memory (file-based tmp) SQLite database pre-populated with test rows."""
    db_file = str(tmp_path / "test.kismet")
    conn = sqlite3.connect(db_file)
    conn.execute(
        """CREATE TABLE devices (
            devmac TEXT NOT NULL,
            type   TEXT,
            device TEXT,
            last_time INTEGER
        )"""
    )
    now = int(time.time())
    rows = [
        ("AA:BB:CC:DD:EE:01", "Wi-Fi AP",   _make_device_json(),          now - 30),
        ("AA:BB:CC:DD:EE:02", "Wi-Fi Client", _make_device_json("HomeNet"), now - 60),
        ("AA:BB:CC:DD:EE:03", "Wi-Fi Client", _make_device_json("OfficeWi-Fi"), now - 120),
        ("AA:BB:CC:DD:EE:04", "Wi-Fi Client", _make_device_json(),          now - 300),
    ]
    conn.executemany(
        "INSERT INTO devices VALUES (?, ?, ?, ?)", rows
    )
    conn.commit()
    conn.close()
    yield db_file, now


# ---------------------------------------------------------------------------
# SecureKismetDB — connection lifecycle
# ---------------------------------------------------------------------------

class TestSecureKismetDBConnection:

    @pytest.mark.unit
    def test_context_manager_connects_and_closes(self, mem_db):
        db_file, _ = mem_db
        with SecureKismetDB(db_file) as db:
            assert db._connection is not None
        assert db._connection is None

    @pytest.mark.unit
    def test_explicit_connect_close(self, mem_db):
        db_file, _ = mem_db
        db = SecureKismetDB(db_file)
        db.connect()
        assert db._connection is not None
        db.close()
        assert db._connection is None

    @pytest.mark.unit
    def test_connect_raises_on_invalid_path(self, tmp_path):
        # SQLite creates new files automatically; use a path inside a
        # non-existent directory to force an OperationalError.
        db = SecureKismetDB(str(tmp_path / "no_such_dir" / "test.kismet"))
        with pytest.raises(Exception):
            db.connect()

    @pytest.mark.unit
    def test_execute_safe_query_raises_when_not_connected(self, tmp_path):
        db = SecureKismetDB(str(tmp_path / "any.kismet"))
        with pytest.raises(RuntimeError, match="not connected"):
            db.execute_safe_query("SELECT 1")

    @pytest.mark.unit
    def test_factory_function_returns_instance(self, mem_db):
        db_file, _ = mem_db
        db = create_secure_db_connection(db_file)
        assert isinstance(db, SecureKismetDB)


# ---------------------------------------------------------------------------
# SecureKismetDB — get_devices_by_time_range
# ---------------------------------------------------------------------------

class TestGetDevicesByTimeRange:

    @pytest.mark.unit
    def test_returns_all_devices_after_old_timestamp(self, mem_db):
        db_file, now = mem_db
        with SecureKismetDB(db_file) as db:
            devices = db.get_devices_by_time_range(now - 400)
        assert len(devices) == 4

    @pytest.mark.unit
    def test_returns_only_recent_devices(self, mem_db):
        db_file, now = mem_db
        with SecureKismetDB(db_file) as db:
            # Only devices within last 90 seconds
            devices = db.get_devices_by_time_range(now - 90)
        macs = [d["mac"] for d in devices]
        assert "AA:BB:CC:DD:EE:01" in macs
        assert "AA:BB:CC:DD:EE:02" in macs
        assert "AA:BB:CC:DD:EE:04" not in macs

    @pytest.mark.unit
    def test_time_range_upper_bound_respected(self, mem_db):
        db_file, now = mem_db
        with SecureKismetDB(db_file) as db:
            devices = db.get_devices_by_time_range(now - 400, now - 200)
        # Only device at now-300 fits the window
        assert len(devices) == 1
        assert devices[0]["mac"] == "AA:BB:CC:DD:EE:04"

    @pytest.mark.unit
    def test_device_dict_structure(self, mem_db):
        db_file, now = mem_db
        with SecureKismetDB(db_file) as db:
            devices = db.get_devices_by_time_range(now - 400)
        for d in devices:
            assert "mac" in d
            assert "type" in d
            assert "device_data" in d
            assert "last_time" in d


# ---------------------------------------------------------------------------
# SecureKismetDB — get_mac_addresses_by_time_range
# ---------------------------------------------------------------------------

class TestGetMACAddresses:

    @pytest.mark.unit
    def test_returns_list_of_strings(self, mem_db):
        db_file, now = mem_db
        with SecureKismetDB(db_file) as db:
            macs = db.get_mac_addresses_by_time_range(now - 400)
        assert all(isinstance(m, str) for m in macs)
        assert len(macs) == 4

    @pytest.mark.unit
    def test_no_devices_returns_empty_list(self, mem_db):
        db_file, now = mem_db
        with SecureKismetDB(db_file) as db:
            macs = db.get_mac_addresses_by_time_range(now + 9999)
        assert macs == []


# ---------------------------------------------------------------------------
# SecureKismetDB — get_probe_requests_by_time_range
# ---------------------------------------------------------------------------

class TestGetProbeRequests:

    @pytest.mark.unit
    def test_returns_only_devices_with_ssids(self, mem_db):
        db_file, now = mem_db
        with SecureKismetDB(db_file) as db:
            probes = db.get_probe_requests_by_time_range(now - 400)
        ssids = [p["ssid"] for p in probes]
        assert "HomeNet" in ssids
        assert "OfficeWi-Fi" in ssids
        # Devices without SSID should not appear
        assert len(probes) == 2

    @pytest.mark.unit
    def test_probe_dict_structure(self, mem_db):
        db_file, now = mem_db
        with SecureKismetDB(db_file) as db:
            probes = db.get_probe_requests_by_time_range(now - 400)
        for p in probes:
            assert "mac" in p
            assert "ssid" in p
            assert "timestamp" in p

    @pytest.mark.unit
    def test_malformed_device_json_skipped_gracefully(self, tmp_path):
        db_file = str(tmp_path / "bad.kismet")
        now = int(time.time())
        conn = sqlite3.connect(db_file)
        conn.execute(
            "CREATE TABLE devices (devmac TEXT, type TEXT, device TEXT, last_time INTEGER)"
        )
        conn.execute(
            "INSERT INTO devices VALUES (?, ?, ?, ?)",
            ("BB:CC:DD:EE:FF:00", "Wi-Fi Client", "NOT VALID JSON {{{", now - 10),
        )
        conn.commit()
        conn.close()

        with SecureKismetDB(db_file) as db:
            # Should not raise — malformed rows are skipped
            probes = db.get_probe_requests_by_time_range(now - 60)
        assert probes == []


# ---------------------------------------------------------------------------
# SecureKismetDB — validate_connection
# ---------------------------------------------------------------------------

class TestValidateConnection:

    @pytest.mark.unit
    def test_valid_db_returns_true(self, mem_db):
        db_file, _ = mem_db
        with SecureKismetDB(db_file) as db:
            assert db.validate_connection() is True

    @pytest.mark.unit
    def test_invalid_schema_returns_false(self, tmp_path):
        db_file = str(tmp_path / "empty.kismet")
        conn = sqlite3.connect(db_file)
        conn.execute("CREATE TABLE other (id INTEGER)")
        conn.commit()
        conn.close()
        with SecureKismetDB(db_file) as db:
            assert db.validate_connection() is False


# ---------------------------------------------------------------------------
# SecureTimeWindows
# ---------------------------------------------------------------------------

SAMPLE_CONFIG = {
    "timing": {
        "time_windows": {
            "recent": 5,
            "medium": 10,
            "old": 15,
            "oldest": 20,
        }
    }
}


class TestSecureTimeWindows:

    @pytest.mark.unit
    def test_get_time_boundaries_returns_all_windows(self):
        stw = SecureTimeWindows(SAMPLE_CONFIG)
        boundaries = stw.get_time_boundaries()
        for key in ("recent_time", "medium_time", "old_time", "oldest_time", "current_time"):
            assert key in boundaries
            assert isinstance(boundaries[key], float)

    @pytest.mark.unit
    def test_window_ordering(self):
        """Older windows should have smaller (earlier) timestamps."""
        stw = SecureTimeWindows(SAMPLE_CONFIG)
        b = stw.get_time_boundaries()
        assert b["recent_time"] > b["medium_time"] > b["old_time"] > b["oldest_time"]

    @pytest.mark.unit
    def test_defaults_used_when_no_config(self):
        stw = SecureTimeWindows({})
        boundaries = stw.get_time_boundaries()
        assert "recent_time" in boundaries

    @pytest.mark.unit
    def test_filter_devices_removes_ignored(self):
        stw = SecureTimeWindows(SAMPLE_CONFIG)
        devices = ["AA:BB:CC:DD:EE:01", "AA:BB:CC:DD:EE:02", "FF:FF:FF:FF:FF:FF"]
        ignore = ["AA:BB:CC:DD:EE:01", "FF:FF:FF:FF:FF:FF"]
        result = stw.filter_devices_by_ignore_list(devices, ignore)
        assert result == ["AA:BB:CC:DD:EE:02"]

    @pytest.mark.unit
    def test_filter_devices_case_insensitive(self):
        stw = SecureTimeWindows(SAMPLE_CONFIG)
        devices = ["aa:bb:cc:dd:ee:ff"]
        ignore = ["AA:BB:CC:DD:EE:FF"]
        result = stw.filter_devices_by_ignore_list(devices, ignore)
        assert result == []

    @pytest.mark.unit
    def test_filter_devices_empty_ignore_list(self):
        stw = SecureTimeWindows(SAMPLE_CONFIG)
        devices = ["AA:BB:CC:DD:EE:01"]
        result = stw.filter_devices_by_ignore_list(devices, [])
        assert result == devices

    @pytest.mark.unit
    def test_filter_ssids_removes_ignored(self):
        stw = SecureTimeWindows(SAMPLE_CONFIG)
        ssids = ["HomeNet", "OfficeWi-Fi", "GuestNet"]
        ignore = ["HomeNet", "GuestNet"]
        result = stw.filter_ssids_by_ignore_list(ssids, ignore)
        assert result == ["OfficeWi-Fi"]

    @pytest.mark.unit
    def test_filter_ssids_empty_ignore_list(self):
        stw = SecureTimeWindows(SAMPLE_CONFIG)
        ssids = ["HomeNet"]
        result = stw.filter_ssids_by_ignore_list(ssids, [])
        assert result == ssids
