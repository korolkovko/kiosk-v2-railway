# test_kiosk_configuration.py
# Tests for kiosk-specific configuration system

import pytest
import tempfile
import yaml
from pathlib import Path

from app.kiosk_configuration_service import KioskConfigurationService, KioskUtilityConfig, KioskIntegrationsConfig


class TestKioskConfigurationService:
    """Test kiosk configuration service functionality"""
    
    def setup_method(self):
        """Set up test configuration file"""
        self.test_config = {
            'kiosk_001': {
                'POS_TERMINAL_ID': 'POS_001',
                'POS_TERMINAL_ADDRESS': '192.168.1.100:8080',
                'POS_TERMINAL_TIMEOUT': 45,
                'POS_TERMINAL_RETRY': 5,
                
                'FISCAL_DEVICE_ID': 'FISCAL_001',
                'FISCAL_DEVICE_ADDRESS': '192.168.1.101:9090',
                'FISCAL_DEVICE_TIMEOUT': 25,
                'FISCAL_DEVICE_RETRY': 3,
                
                'PRINTER_DEVICE_ID': 'PRINTER_001',
                'PRINTER_DEVICE_ADDRESS': '192.168.1.102:515',
                'PRINTER_DEVICE_TIMEOUT': 15,
                'PRINTER_DEVICE_RETRY': 2,
                
                'KDS_NAME': 'Kitchen_Station_A',
                'KDS_ADDRESS': '192.168.1.103:3000',
                'KDS_TIMEOUT': 20,
                'KDS_RETRY': 3
            },
            'kiosk_002': {
                'POS_TERMINAL_ID': 'POS_002',
                'POS_TERMINAL_ADDRESS': '192.168.1.200:8080',
                'POS_TERMINAL_TIMEOUT': 30,
                'POS_TERMINAL_RETRY': 3
            }
        }
        
        # Create temporary config file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.test_config, self.temp_file, default_flow_style=False)
        self.temp_file.close()
        
        # Create service with test config file
        self.service = KioskConfigurationService(self.temp_file.name)
    
    def teardown_method(self):
        """Clean up test files"""
        Path(self.temp_file.name).unlink(missing_ok=True)
    
    def test_get_kiosk_config_existing(self):
        """Test getting configuration for existing kiosk"""
        config = self.service.get_kiosk_config('kiosk_001')
        
        assert config is not None
        assert config.kiosk_username == 'kiosk_001'
        assert config.pos_terminal_id == 'POS_001'
        assert config.pos_terminal_config.address == '192.168.1.100:8080'
        assert config.pos_terminal_config.timeout == 45
        assert config.pos_terminal_config.retry_count == 5
    
    def test_get_kiosk_config_nonexistent(self):
        """Test getting configuration for non-existent kiosk"""
        config = self.service.get_kiosk_config('kiosk_999')
        assert config is None
    
    def test_get_pos_terminal_config(self):
        """Test getting POS terminal configuration"""
        terminal_id, terminal_config = self.service.get_pos_terminal_config('kiosk_001')
        
        assert terminal_id == 'POS_001'
        assert terminal_config.address == '192.168.1.100:8080'
        assert terminal_config.timeout == 45
        assert terminal_config.retry_count == 5
    
    def test_get_fiscal_device_config(self):
        """Test getting fiscal device configuration"""
        device_id, device_config = self.service.get_fiscal_device_config('kiosk_001')
        
        assert device_id == 'FISCAL_001'
        assert device_config.address == '192.168.1.101:9090'
        assert device_config.timeout == 25
        assert device_config.retry_count == 3
    
    def test_get_kds_config(self):
        """Test getting KDS configuration"""
        kds_name, kds_config = self.service.get_kds_config('kiosk_001')
        
        assert kds_name == 'Kitchen_Station_A'
        assert kds_config.address == '192.168.1.103:3000'
        assert kds_config.timeout == 20
        assert kds_config.retry_count == 3
    
    def test_validate_kiosk_config_valid(self):
        """Test validation for valid kiosk configuration"""
        validation = self.service.validate_kiosk_config('kiosk_001')
        
        assert validation['valid'] is True
        assert len(validation['issues']) == 0
        assert validation['config_summary']['pos_terminal_id'] == 'POS_001'
        assert validation['config_summary']['has_pos_config'] is True
    
    def test_validate_kiosk_config_partial(self):
        """Test validation for partially configured kiosk"""
        validation = self.service.validate_kiosk_config('kiosk_002')
        
        # kiosk_002 only has POS terminal configured
        assert validation['config_summary']['has_pos_config'] is True
        assert validation['config_summary']['has_fiscal_config'] is False
        assert validation['config_summary']['has_printer_config'] is False
        assert validation['config_summary']['has_kds_config'] is False
    
    def test_validate_kiosk_config_nonexistent(self):
        """Test validation for non-existent kiosk"""
        validation = self.service.validate_kiosk_config('kiosk_999')
        
        assert validation['valid'] is False
        assert 'No configuration found for kiosk kiosk_999' in validation['issues']
    
    def test_get_all_configured_kiosks(self):
        """Test getting list of all configured kiosks"""
        kiosks = self.service.get_all_configured_kiosks()
        
        assert 'kiosk_001' in kiosks
        assert 'kiosk_002' in kiosks
        assert len(kiosks) == 2
    
    def test_validate_all_kiosks(self):
        """Test validation for all kiosks"""
        validation = self.service.validate_all_kiosks()
        
        assert 'kiosk_001' in validation['kiosk_results']
        assert 'kiosk_002' in validation['kiosk_results']
        assert validation['total_kiosks'] == 2
    
    def test_cache_functionality(self):
        """Test that configuration caching works"""
        # First call should initialize cache
        config1 = self.service.get_kiosk_config('kiosk_001')
        
        # Second call should use cache
        config2 = self.service.get_kiosk_config('kiosk_001')
        
        # Should be the same object due to caching
        assert config1 is config2
    
    def test_refresh_cache(self):
        """Test cache refresh functionality"""
        # Get initial config
        config1 = self.service.get_kiosk_config('kiosk_001')
        
        # Refresh cache
        self.service.refresh_cache()
        
        # Get config again - should be different object
        config2 = self.service.get_kiosk_config('kiosk_001')
        
        # Should be different objects but same content
        assert config1 is not config2
        assert config1.kiosk_username == config2.kiosk_username