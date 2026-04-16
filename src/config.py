"""
config.py - Load and validate user-defined configuration from YAML.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "smart-file-organizer" / "config.yaml"
LOCAL_CONFIG_PATH = Path("config.yaml")

VALID_KEYS = {"rules", "watch_folder", "silent", "dry_run", "notifications"}


def load_config(config_path: str = None) -> dict:
    """
    Load configuration from YAML file.

    Search order:
    1. Explicitly provided path
    2. ./config.yaml (local project config)
    3. ~/.config/smart-file-organizer/config.yaml
    4. Empty defaults

    Returns:
        Config dict (always valid, even if no file found).
    """
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not installed. Using defaults.")
        return {}

    paths_to_try = []
    if config_path:
        paths_to_try.append(Path(config_path))
    paths_to_try.extend([LOCAL_CONFIG_PATH, DEFAULT_CONFIG_PATH])

    for path in paths_to_try:
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                _validate(data, path)
                logger.info(f"Loaded config from {path}")
                return data
            except Exception as e:
                logger.warning(f"Could not load config from {path}: {e}")

    return {}


def _validate(config: dict, path: Path):
    """Warn about unknown keys in config."""
    for key in config:
        if key not in VALID_KEYS:
            logger.warning(f"Unknown config key '{key}' in {path}. Valid keys: {VALID_KEYS}")

    rules = config.get("rules", {})
    if not isinstance(rules, dict):
        raise ValueError(f"'rules' must be a mapping (dict) in {path}")

    for ext, folder in rules.items():
        if not ext.startswith("."):
            logger.warning(f"Config rule key '{ext}' should start with '.' (e.g. '.mp4')")
        if not isinstance(folder, str):
            raise ValueError(f"Rule value for '{ext}' must be a string folder name")

    if "notifications" in config and not isinstance(config["notifications"], bool):
        raise ValueError(f"'notifications' must be true or false in {path}")
