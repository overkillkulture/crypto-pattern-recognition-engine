"""Configuration management utilities."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from loguru import logger


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment variable substitution.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    path = Path(config_path)

    if not path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return get_default_config()

    with open(path, 'r') as f:
        config_content = f.read()

    # Replace environment variables
    config_content = _substitute_env_vars(config_content)

    config = yaml.safe_load(config_content)
    logger.info(f"Configuration loaded from {config_path}")

    return config


def _substitute_env_vars(content: str) -> str:
    """Substitute ${VAR} patterns with environment variables."""
    import re

    pattern = r'\$\{([^}]+)\}'

    def replacer(match):
        var_name = match.group(1)
        return os.getenv(var_name, '')

    return re.sub(pattern, replacer, content)


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration.

    Args:
        config: Configuration to validate

    Returns:
        True if valid, raises ValueError otherwise
    """
    required_sections = ['exchanges', 'pairs', 'timeframes', 'patterns']

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: {section}")

    # Validate pairs
    if not config['pairs']:
        raise ValueError("No trading pairs configured")

    # Validate timeframes
    if not config['timeframes']:
        raise ValueError("No timeframes configured")

    logger.info("Configuration validated successfully")
    return True


def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return {
        'exchanges': {
            'binance': {
                'enabled': True,
                'rate_limit': 1200,
            }
        },
        'pairs': ['BTC/USDT'],
        'timeframes': ['1h'],
        'patterns': {
            'technical_indicators': {
                'enabled': True,
                'indicators': ['rsi', 'macd'],
            }
        },
        'alerts': {
            'enabled': True,
            'channels': {
                'console': {'enabled': True}
            },
            'filters': {
                'min_confidence': 0.75,
            }
        },
        'logging': {
            'level': 'INFO',
        },
        'realtime': {
            'enabled': False,
            'update_interval': 60,
        }
    }


def get_exchange_config(config: Dict[str, Any], exchange: str) -> Dict[str, Any]:
    """Get configuration for a specific exchange."""
    exchanges = config.get('exchanges', {})
    return exchanges.get(exchange, {})


def is_exchange_enabled(config: Dict[str, Any], exchange: str) -> bool:
    """Check if an exchange is enabled."""
    exchange_config = get_exchange_config(config, exchange)
    return exchange_config.get('enabled', False)
