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
    Load configuration from YAML file with validation.

    Search order:
    1. Explicitly provided path
    2. ./config.yaml
    3. ~/.config/smart-file-organizer/config.yaml
    4. Fallback to defaults

    Returns:
        Valid config dict
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
                    config = yaml.safe_load(f) or {}

                validate_config(config, path)

                logger.info(f"Loaded config from {path}")
                return config

            except Exception as e:
                logger.error(f"Invalid config in {path}: {e}")
                logger.warning("Falling back to default configuration.")
                return {}

    return {}


def validate_config(config: dict, path: Path):
    """
    Validate full config structure.
    Raises ValueError if invalid.
    """

    # ✅ Top-level check
    if not isinstance(config, dict):
        raise ValueError(f"Config must be a dictionary in {path}")

    # ✅ Unknown keys warning
    for key in config:
        if key not in VALID_KEYS:
            logger.warning(
                f"Unknown config key '{key}' in {path}. Valid keys: {VALID_KEYS}"
            )

    # ✅ Validate rules
    rules = config.get("rules", {})
    if not isinstance(rules, dict):
        raise ValueError(f"'rules' must be a dictionary in {path}")

    for key, value in rules.items():
        if not isinstance(key, str):
            raise ValueError(f"Rule key '{key}' must be a string in {path}")

        if not key.startswith("."):
            logger.warning(
                f"Rule key '{key}' should start with '.' (e.g. '.mp4')"
            )

        if not isinstance(value, str):
            raise ValueError(
                f"Rule value for '{key}' must be a string folder name in {path}"
            )

    # ✅ Validate watch_folder
    watch_folder = config.get("watch_folder")
    if watch_folder is not None and not isinstance(watch_folder, str):
        raise ValueError(f"'watch_folder' must be a string path in {path}")

    # ✅ Validate silent
    silent = config.get("silent")
    if silent is not None and not isinstance(silent, bool):
        raise ValueError(f"'silent' must be a boolean in {path}")

    # ✅ Validate dry_run
    dry_run = config.get("dry_run")
    if dry_run is not None and not isinstance(dry_run, bool):
        raise ValueError(f"'dry_run' must be a boolean in {path}")

    notifications = config.get("notifications")
    if notifications is not None and not isinstance(notifications, bool):
        raise ValueError(f"'notifications' must be a boolean in {path}")