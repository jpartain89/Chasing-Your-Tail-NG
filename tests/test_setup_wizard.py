"""
Tests for setup_wizard.py
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from setup_wizard import SetupConfig, needs_setup, CLISetupWizard


class TestSetupConfig:
    """Test SetupConfig class"""
    
    def test_default_config_creation(self, tmp_path):
        """Test that default config is created correctly"""
        config_file = tmp_path / "test_config.json"
        config = SetupConfig(str(config_file))
        
        assert config.config is not None
        assert 'paths' in config.config
        assert 'timing' in config.config
        assert 'search' in config.config
    
    def test_config_has_required_paths(self, tmp_path):
        """Test that config contains required path entries"""
        config_file = tmp_path / "test_config.json"
        config = SetupConfig(str(config_file))
        
        assert 'base_dir' in config.config['paths']
        assert 'log_dir' in config.config['paths']
        assert 'kismet_logs' in config.config['paths']
        assert 'ignore_lists' in config.config['paths']
    
    def test_config_has_timing_settings(self, tmp_path):
        """Test that config contains timing settings"""
        config_file = tmp_path / "test_config.json"
        config = SetupConfig(str(config_file))
        
        assert 'check_interval' in config.config['timing']
        assert 'list_update_interval' in config.config['timing']
        assert 'time_windows' in config.config['timing']
    
    def test_config_save_and_load(self, tmp_path):
        """Test saving and loading config"""
        config_file = tmp_path / "test_config.json"
        config = SetupConfig(str(config_file))
        
        # Modify config
        config.config['paths']['kismet_logs'] = '/test/path/*.kismet'
        
        # Save
        assert config.save_config() is True
        
        # Load again
        config2 = SetupConfig(str(config_file))
        assert config2.config['paths']['kismet_logs'] == '/test/path/*.kismet'
    
    def test_setup_complete_flag(self, tmp_path):
        """Test setup complete flag"""
        config_file = tmp_path / "test_config.json"
        config = SetupConfig(str(config_file))
        
        # Initially not complete
        assert config.is_setup_complete() is False
        
        # Mark as complete
        config.mark_setup_complete()
        
        # Should be complete now
        assert config.is_setup_complete() is True
        
        # Verify it persists
        config2 = SetupConfig(str(config_file))
        assert config2.is_setup_complete() is True
    
    def test_merge_configs(self, tmp_path):
        """Test config merging preserves user settings"""
        config_file = tmp_path / "test_config.json"
        
        # Create initial config with custom values
        initial_config = {
            'paths': {
                'kismet_logs': '/custom/path/*.kismet'
            },
            'timing': {
                'check_interval': 120
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(initial_config, f)
        
        # Load config (should merge with defaults)
        config = SetupConfig(str(config_file))
        
        # Custom values should be preserved
        assert config.config['paths']['kismet_logs'] == '/custom/path/*.kismet'
        assert config.config['timing']['check_interval'] == 120
        
        # But defaults should still be present
        assert 'log_dir' in config.config['paths']
        assert 'list_update_interval' in config.config['timing']


class TestNeedsSetup:
    """Test needs_setup function"""
    
    def test_needs_setup_when_incomplete(self, tmp_path, monkeypatch):
        """Test needs_setup returns True when setup is incomplete"""
        config_file = tmp_path / "config.json"
        
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Create config without setup_complete flag
        with open(config_file, 'w') as f:
            json.dump({'paths': {}, 'timing': {}}, f)
        
        assert needs_setup() is True
    
    def test_needs_setup_when_complete(self, tmp_path, monkeypatch):
        """Test needs_setup returns False when setup is complete"""
        config_file = tmp_path / "config.json"
        
        # Change to temp directory
        monkeypatch.chdir(tmp_path)
        
        # Create config with setup_complete flag
        with open(config_file, 'w') as f:
            json.dump({'paths': {}, 'timing': {}, 'setup_complete': True}, f)
        
        assert needs_setup() is False


class TestCLISetupWizard:
    """Test CLISetupWizard class"""
    
    def test_wizard_initialization(self, tmp_path):
        """Test wizard initializes correctly"""
        config_file = tmp_path / "test_config.json"
        config = SetupConfig(str(config_file))
        wizard = CLISetupWizard(config)
        
        assert wizard.config is not None
        assert wizard.config == config
    
    def test_get_input_with_default(self, tmp_path, monkeypatch):
        """Test get_input with default value"""
        config_file = tmp_path / "test_config.json"
        config = SetupConfig(str(config_file))
        wizard = CLISetupWizard(config)
        
        # Simulate empty input (should use default)
        monkeypatch.setattr('builtins.input', lambda _: '')
        result = wizard.get_input("Test prompt", default="default_value")
        
        assert result == "default_value"
    
    def test_get_yes_no_default_yes(self, tmp_path, monkeypatch):
        """Test get_yes_no with default yes"""
        config_file = tmp_path / "test_config.json"
        config = SetupConfig(str(config_file))
        wizard = CLISetupWizard(config)
        
        # Simulate empty input (should use default)
        monkeypatch.setattr('builtins.input', lambda _: '')
        result = wizard.get_yes_no("Test question?", default=True)
        
        assert result is True
    
    def test_get_yes_no_explicit_yes(self, tmp_path, monkeypatch):
        """Test get_yes_no with explicit yes"""
        config_file = tmp_path / "test_config.json"
        config = SetupConfig(str(config_file))
        wizard = CLISetupWizard(config)
        
        # Simulate 'y' input
        monkeypatch.setattr('builtins.input', lambda _: 'y')
        result = wizard.get_yes_no("Test question?", default=False)
        
        assert result is True
    
    def test_get_yes_no_explicit_no(self, tmp_path, monkeypatch):
        """Test get_yes_no with explicit no"""
        config_file = tmp_path / "test_config.json"
        config = SetupConfig(str(config_file))
        wizard = CLISetupWizard(config)
        
        # Simulate 'n' input
        monkeypatch.setattr('builtins.input', lambda _: 'n')
        result = wizard.get_yes_no("Test question?", default=True)
        
        assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
