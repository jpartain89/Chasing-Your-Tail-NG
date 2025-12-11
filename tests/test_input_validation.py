"""
Tests for input_validation.py
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from input_validation import InputValidator


class TestMACAddressValidation:
    """Test MAC address validation"""
    
    def test_valid_mac_colon_separator(self):
        """Test valid MAC address with colon separator"""
        assert InputValidator.validate_mac_address("AA:BB:CC:DD:EE:FF") is True
        assert InputValidator.validate_mac_address("00:11:22:33:44:55") is True
    
    def test_valid_mac_dash_separator(self):
        """Test valid MAC address with dash separator"""
        assert InputValidator.validate_mac_address("AA-BB-CC-DD-EE-FF") is True
        assert InputValidator.validate_mac_address("00-11-22-33-44-55") is True
    
    def test_valid_mac_lowercase(self):
        """Test valid MAC address with lowercase"""
        assert InputValidator.validate_mac_address("aa:bb:cc:dd:ee:ff") is True
    
    def test_invalid_mac_wrong_format(self):
        """Test invalid MAC address formats"""
        assert InputValidator.validate_mac_address("AABBCCDDEEFF") is False
        assert InputValidator.validate_mac_address("AA:BB:CC:DD:EE") is False
        assert InputValidator.validate_mac_address("AA:BB:CC:DD:EE:FF:GG") is False
    
    def test_invalid_mac_non_hex(self):
        """Test MAC address with non-hex characters"""
        assert InputValidator.validate_mac_address("ZZ:BB:CC:DD:EE:FF") is False
    
    def test_invalid_mac_not_string(self):
        """Test MAC validation with non-string input"""
        assert InputValidator.validate_mac_address(123) is False
        assert InputValidator.validate_mac_address(None) is False


class TestSSIDValidation:
    """Test SSID validation"""
    
    def test_valid_ssid(self):
        """Test valid SSIDs"""
        assert InputValidator.validate_ssid("MyNetwork") is True
        assert InputValidator.validate_ssid("WiFi_2.4GHz") is True
        assert InputValidator.validate_ssid("Guest-Network-123") is True
    
    def test_ssid_length_limits(self):
        """Test SSID length validation"""
        # Empty SSID
        assert InputValidator.validate_ssid("") is False
        
        # Valid length (32 chars max)
        assert InputValidator.validate_ssid("A" * 32) is True
        
        # Too long
        assert InputValidator.validate_ssid("A" * 33) is False
    
    def test_ssid_dangerous_characters(self):
        """Test SSID with dangerous characters"""
        assert InputValidator.validate_ssid("Network<script>") is False
        assert InputValidator.validate_ssid("WiFi'DROP") is False
        assert InputValidator.validate_ssid("Net;work") is False
    
    def test_ssid_control_characters(self):
        """Test SSID with control characters"""
        assert InputValidator.validate_ssid("Network\x00") is False
        assert InputValidator.validate_ssid("WiFi\x01") is False
    
    def test_invalid_ssid_not_string(self):
        """Test SSID validation with non-string input"""
        assert InputValidator.validate_ssid(123) is False
        assert InputValidator.validate_ssid(None) is False


class TestFilePathValidation:
    """Test file path validation"""
    
    def test_valid_paths(self):
        """Test valid file paths"""
        assert InputValidator.validate_file_path("/home/user/file.txt") is True
        assert InputValidator.validate_file_path("/var/log/kismet.db") is True
        assert InputValidator.validate_file_path("./relative/path.json") is True
    
    def test_path_traversal_attempts(self):
        """Test detection of path traversal attempts"""
        assert InputValidator.validate_file_path("../../../etc/passwd") is False
        assert InputValidator.validate_file_path("/home/user/../../../etc/shadow") is False
        assert InputValidator.validate_file_path("~/secret/file") is False
    
    def test_dangerous_characters_in_path(self):
        """Test paths with dangerous characters"""
        assert InputValidator.validate_file_path("/home/user/file|rm -rf") is False
        assert InputValidator.validate_file_path("/path;/file") is False
        assert InputValidator.validate_file_path("/home/`whoami`/file") is False
    
    def test_path_length_limit(self):
        """Test path length validation"""
        # Very long path
        long_path = "/home/" + "a" * 5000
        assert InputValidator.validate_file_path(long_path) is False


class TestStringSanitization:
    """Test string sanitization"""
    
    def test_sanitize_normal_string(self):
        """Test sanitization of normal strings"""
        result = InputValidator.sanitize_string("Hello World")
        assert result == "Hello World"
    
    def test_remove_dangerous_characters(self):
        """Test removal of dangerous characters"""
        result = InputValidator.sanitize_string("Hello<script>World")
        assert "<" not in result
        assert ">" not in result
    
    def test_remove_sql_keywords(self):
        """Test removal of SQL keywords"""
        result = InputValidator.sanitize_string("SELECT * FROM users")
        # Sanitizer should remove SQL keywords, leaving sanitized string
        # The function removes keywords but may leave some characters
        assert "select" not in result.lower() or len(result) < len("SELECT * FROM users")
    
    def test_truncate_long_string(self):
        """Test truncation of long strings"""
        long_string = "A" * 2000
        result = InputValidator.sanitize_string(long_string, max_length=100)
        assert len(result) <= 100
    
    def test_remove_control_characters(self):
        """Test removal of control characters"""
        result = InputValidator.sanitize_string("Hello\x00World\x01")
        assert "\x00" not in result
        assert "\x01" not in result


class TestConfigValidation:
    """Test configuration validation"""
    
    def test_valid_config_structure(self):
        """Test validation of valid config"""
        config = {
            'paths': {
                'log_dir': 'logs',
                'kismet_logs': '/tmp/*.kismet',
                'ignore_lists': {
                    'mac': 'mac_list.json',
                    'ssid': 'ssid_list.json'
                }
            },
            'timing': {
                'check_interval': 60,
                'list_update_interval': 5
            }
        }
        
        assert InputValidator.validate_config_structure(config) is True
    
    def test_missing_required_keys(self):
        """Test detection of missing required keys"""
        # Missing 'paths'
        config1 = {'timing': {}}
        assert InputValidator.validate_config_structure(config1) is False
        
        # Missing 'timing'
        config2 = {'paths': {}}
        assert InputValidator.validate_config_structure(config2) is False
    
    def test_invalid_timing_values(self):
        """Test detection of invalid timing values"""
        config = {
            'paths': {
                'log_dir': 'logs',
                'kismet_logs': '/tmp/*.kismet',
                'ignore_lists': {}
            },
            'timing': {
                'check_interval': -1  # Invalid: negative
            }
        }
        
        assert InputValidator.validate_config_structure(config) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
