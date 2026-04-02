"""Tests for secure_credentials.py — SecureCredentialManager and secure_config_loader."""

import json
import os
import sys

import pytest

# Ensure test mode is active before any import of credential modules.
os.environ["CYT_TEST_MODE"] = "true"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from secure_credentials import (
    SecureCredentialManager,
    get_environment_credentials,
    secure_config_loader,
)


# ---------------------------------------------------------------------------
# SecureCredentialManager — store and retrieve
# ---------------------------------------------------------------------------

class TestSecureCredentialManager:

    @pytest.fixture()
    def cred_dir(self, tmp_path):
        """Temporary credential directory for each test."""
        return str(tmp_path / "creds")

    @pytest.mark.unit
    def test_store_and_retrieve_credential(self, cred_dir):
        mgr = SecureCredentialManager(credentials_dir=cred_dir)
        mgr.store_credential("wigle", "encoded_token", "abc123token")
        result = mgr.get_credential("wigle", "encoded_token")
        assert result == "abc123token"

    @pytest.mark.unit
    def test_overwrite_credential(self, cred_dir):
        mgr = SecureCredentialManager(credentials_dir=cred_dir)
        mgr.store_credential("wigle", "encoded_token", "first_value")
        mgr.store_credential("wigle", "encoded_token", "second_value")
        result = mgr.get_credential("wigle", "encoded_token")
        assert result == "second_value"

    @pytest.mark.unit
    def test_get_missing_credential_returns_none(self, cred_dir):
        mgr = SecureCredentialManager(credentials_dir=cred_dir)
        result = mgr.get_credential("noservice", "notype")
        assert result is None

    @pytest.mark.unit
    def test_get_credential_when_no_file_returns_none(self, cred_dir):
        mgr = SecureCredentialManager(credentials_dir=cred_dir)
        # No store_credential called — file doesn't exist.
        result = mgr.get_credential("wigle", "encoded_token")
        assert result is None

    @pytest.mark.unit
    def test_multiple_services_stored_independently(self, cred_dir):
        mgr = SecureCredentialManager(credentials_dir=cred_dir)
        mgr.store_credential("wigle", "token", "wigle_val")
        mgr.store_credential("othersvc", "key", "other_val")
        assert mgr.get_credential("wigle", "token") == "wigle_val"
        assert mgr.get_credential("othersvc", "key") == "other_val"

    @pytest.mark.unit
    def test_store_validates_non_string_raises(self, cred_dir):
        mgr = SecureCredentialManager(credentials_dir=cred_dir)
        with pytest.raises(ValueError):
            mgr.store_credential("svc", "key", 12345)  # type: ignore[arg-type]

    @pytest.mark.unit
    def test_store_empty_value_raises(self, cred_dir):
        mgr = SecureCredentialManager(credentials_dir=cred_dir)
        with pytest.raises(ValueError):
            mgr.store_credential("svc", "key", "")

    @pytest.mark.unit
    def test_get_wigle_token_convenience(self, cred_dir):
        mgr = SecureCredentialManager(credentials_dir=cred_dir)
        mgr.store_credential("wigle", "encoded_token", "token_xyz")
        assert mgr.get_wigle_token() == "token_xyz"

    @pytest.mark.unit
    def test_credentials_dir_created_with_restricted_permissions(self, tmp_path):
        cred_path = tmp_path / "new_creds"
        assert not cred_path.exists()
        SecureCredentialManager(credentials_dir=str(cred_path))
        assert cred_path.exists()
        # Directory should have restricted permissions (owner only on Unix).
        if os.name == "posix":
            mode = oct(cred_path.stat().st_mode)[-3:]
            assert mode == "700"

    @pytest.mark.unit
    def test_credential_file_has_restricted_permissions(self, cred_dir):
        mgr = SecureCredentialManager(credentials_dir=cred_dir)
        mgr.store_credential("wigle", "encoded_token", "secret")
        if os.name == "posix":
            cred_file = mgr.credentials_file
            mode = oct(cred_file.stat().st_mode)[-3:]
            assert mode == "600"


# ---------------------------------------------------------------------------
# get_environment_credentials
# ---------------------------------------------------------------------------

class TestGetEnvironmentCredentials:

    @pytest.mark.unit
    def test_returns_dict_with_expected_keys(self):
        creds = get_environment_credentials()
        assert "wigle_token" in creds
        assert "db_password" in creds

    @pytest.mark.unit
    def test_picks_up_wigle_token_from_env(self, monkeypatch):
        monkeypatch.setenv("WIGLE_API_TOKEN", "test_wigle_123")
        creds = get_environment_credentials()
        assert creds["wigle_token"] == "test_wigle_123"

    @pytest.mark.unit
    def test_missing_env_vars_return_none(self, monkeypatch):
        monkeypatch.delenv("WIGLE_API_TOKEN", raising=False)
        monkeypatch.delenv("CYT_DB_PASSWORD", raising=False)
        creds = get_environment_credentials()
        assert creds["wigle_token"] is None
        assert creds["db_password"] is None


# ---------------------------------------------------------------------------
# secure_config_loader
# ---------------------------------------------------------------------------

class TestSecureConfigLoader:

    @pytest.mark.unit
    def test_loads_minimal_config(self, tmp_path):
        cfg = {
            "paths": {
                "base_dir": ".",
                "log_dir": "logs",
                "kismet_logs": "/tmp/*.kismet",
                "ignore_lists": {"mac": "mac_list.json", "ssid": "ssid_list.json"},
            },
            "timing": {"check_interval": 60},
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(cfg))

        result_config, cred_mgr = secure_config_loader(str(config_file))

        assert result_config["paths"]["log_dir"] == "logs"
        assert isinstance(cred_mgr, SecureCredentialManager)

    @pytest.mark.unit
    def test_config_with_api_keys_migrates_and_strips_keys(self, tmp_path, monkeypatch):
        """Config containing api_keys should have them stripped after migration."""
        mgr_calls = {}

        # Patch SecureCredentialManager.migrate_from_config to avoid real file writes.
        import secure_credentials as sc_module

        original_migrate = sc_module.SecureCredentialManager.migrate_from_config

        def fake_migrate(self, config):
            mgr_calls["called"] = True

        monkeypatch.setattr(sc_module.SecureCredentialManager, "migrate_from_config", fake_migrate)

        cfg = {
            "paths": {
                "base_dir": ".",
                "log_dir": "logs",
                "kismet_logs": "/tmp/*.kismet",
                "ignore_lists": {"mac": "x.json", "ssid": "y.json"},
            },
            "api_keys": {"wigle": {"encoded_token": "rawtoken123"}},
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(cfg))

        result_config, _ = secure_config_loader(str(config_file))

        assert "api_keys" not in result_config
        assert mgr_calls.get("called") is True

    @pytest.mark.unit
    def test_missing_config_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            secure_config_loader(str(tmp_path / "missing.json"))
