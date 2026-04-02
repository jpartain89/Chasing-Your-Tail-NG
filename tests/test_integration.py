"""
Integration tests for installation and setup
"""
import pytest
import subprocess
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestInstallScript:
    """Test install.sh script"""

    def test_install_script_exists(self):
        """Test that install.sh exists and is executable"""
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'install.sh'
        )
        assert os.path.exists(script_path)
        assert os.access(script_path, os.X_OK)

    def test_install_script_help(self):
        """Test install script --help option"""
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'install.sh'
        )

        result = subprocess.run(
            [script_path, '--help'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert 'Usage:' in result.stdout or 'usage:' in result.stdout.lower()

    def test_install_script_verify(self):
        """Test install script --verify option"""
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'install.sh'
        )

        result = subprocess.run(
            [script_path, '--verify'],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should complete (exit code may vary based on what's installed)
        # Just verify it doesn't crash
        assert result.returncode in [0, 1]


class TestPythonModules:
    """Test that all Python modules can be imported"""

    def test_import_setup_wizard(self):
        """Test importing setup_wizard module"""
        import setup_wizard
        assert hasattr(setup_wizard, 'SetupConfig')
        assert hasattr(setup_wizard, 'CLISetupWizard')

    def test_import_input_validation(self):
        """Test importing input_validation module"""
        import input_validation
        assert hasattr(input_validation, 'InputValidator')

    def test_import_secure_credentials(self):
        """Test importing secure_credentials module"""
        import secure_credentials
        assert hasattr(secure_credentials, 'SecureCredentialManager')

    def test_import_secure_database(self):
        """Test importing secure_database module"""
        import secure_database
        assert hasattr(secure_database, 'SecureKismetDB')

    def test_import_cyt_cli(self):
        """Test importing unified CLI module"""
        import cyt_cli
        assert hasattr(cyt_cli, 'build_parser')

    def test_import_cyt_core_runtime(self):
        """Test importing shared runtime module"""
        import cyt_core_runtime
        assert hasattr(cyt_core_runtime, 'MonitoringService')


class TestConfigSchema:
    """Test that config.json has the expected canonical schema."""

    def test_config_file_exists(self):
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        assert os.path.exists(cfg_path)

    def test_config_has_required_path_keys(self):
        import json
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(cfg_path) as f:
            cfg = json.load(f)
        required_keys = [
            "log_dir",
            "reports_dir",
            "kml_dir",
            "surveillance_reports_dir",
            "analysis_logs_dir",
            "kismet_logs",
        ]
        for key in required_keys:
            assert key in cfg["paths"], f"Missing path key in config.json: {key}"

    def test_setup_config_defaults_include_output_dirs(self):
        import setup_wizard
        defaults = setup_wizard.SetupConfig.DEFAULT_CONFIG
        for key in ("reports_dir", "kml_dir", "surveillance_reports_dir", "analysis_logs_dir"):
            assert key in defaults["paths"], f"Missing default in SetupConfig: {key}"


class TestRequirements:
    """Test requirements.txt"""

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists"""
        req_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'requirements.txt'
        )
        assert os.path.exists(req_path)

    def test_core_dependencies_listed(self):
        """Test that core dependencies are in requirements.txt"""
        req_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'requirements.txt'
        )
        with open(req_path, 'r') as f:
            content = f.read()
        assert 'requests' in content
        assert 'cryptography' in content
