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
        
        # Core dependencies
        assert 'requests' in content
        assert 'cryptography' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
