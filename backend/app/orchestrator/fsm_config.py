# fsm_config.py
# FSM configuration structure - empty for now, will be populated as needed

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class FSMConfig:
    """
    FSM configuration structure for future use.
    Will contain timeout configurations, retry policies, and external service settings.
    """
    
    # State timeout configurations (seconds)
    state_timeouts: Dict[str, int] = None
    
    # Retry policies
    retry_policies: Dict[str, Dict[str, Any]] = None
    
    # External service configurations
    external_services: Dict[str, Dict[str, Any]] = None
    
    # Event handling configurations
    event_handlers: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default empty configurations."""
        if self.state_timeouts is None:
            self.state_timeouts = {}
        
        if self.retry_policies is None:
            self.retry_policies = {}
        
        if self.external_services is None:
            self.external_services = {}
        
        if self.event_handlers is None:
            self.event_handlers = {}


# Global configuration instance - will be loaded from file/environment in the future
fsm_config = FSMConfig()


def load_fsm_config(config_path: Optional[str] = None) -> FSMConfig:
    """
    Load FSM configuration from file or environment.
    For now, returns empty configuration.
    """
    # TODO: Implement configuration loading from YAML/JSON file
    # TODO: Implement environment variable overrides
    # TODO: Implement configuration validation
    return FSMConfig()


def get_fsm_config() -> FSMConfig:
    """Get current FSM configuration."""
    return fsm_config


def update_fsm_config(new_config: FSMConfig) -> None:
    """Update global FSM configuration."""
    global fsm_config
    fsm_config = new_config