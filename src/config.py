"""
config.py - Load and validate user-defined configuration from YAML.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "smart-file-organizer" / "config.yaml"
LOCAL_CONFIG_PATH = Path("config.yaml")

VALID_KEYS = {
    "rules",
    "watch_folder",
    "silent",
    "dry_run",
    "notify",
    "notifications",
    "log_file",
    "organizer_log",
}

DEFAULT_CONFIG = {
    "rules": {},
    "dry_run": True,
    "notify": False,
    "log_file": "organizer_log.json",
}


def load_config(config_path: str = None) -> dict:
    """
    Load configuration from YAML file with validation.
    Falls back to defaults if file is missing or invalid.
    """

    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not installed. Run 'pip install pyyaml'. Using defaults.")
        return DEFAULT_CONFIG.copy()

    paths_to_try = []
    if config_path:
        paths_to_try.append(Path(config_path))
    paths_to_try.extend([LOCAL_CONFIG_PATH, DEFAULT_CONFIG_PATH])

    for path in paths_to_try:
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    file_config = yaml.safe_load(f) or {}

                validate_config(file_config, path)

                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(file_config)

                logger.info(f"Loaded config from {path}")
                return merged_config

            except Exception as e:
                logger.error(f"Invalid config in {path}: {e}")
                logger.warning("Falling back to default configuration.")
                return DEFAULT_CONFIG.copy()

    logger.info("No config file found. Using default configuration.")
    return DEFAULT_CONFIG.copy()


def validate_config(config: dict, path: Path):
    """
    Validate full config structure.
    Raises ValueError if invalid.
    """

    if not isinstance(config, dict):
        raise ValueError(f"Config must be a dictionary in {path}")

    for key in config:
        if key not in VALID_KEYS:
            logger.warning(
                f"Unknown config key '{key}' in {path}. Valid keys: {VALID_KEYS}"
            )

    rules = config.get("rules", {})
    if not isinstance(rules, dict):
        raise ValueError(f"'rules' must be a dictionary in {path}")

    for key, value in rules.items():
        if not isinstance(key, str):
            raise ValueError(f"Rule key '{key}' must be a string in {path}")

        if not key.startswith("."):
            logger.warning(f"Rule key '{key}' should start with '.'")

        if not isinstance(value, str):
            raise ValueError(
                f"Rule value for '{key}' must be a string folder name in {path}"
            )

    watch_folder = config.get("watch_folder")
    if watch_folder is not None and not isinstance(watch_folder, str):
        raise ValueError(f"'watch_folder' must be a string path in {path}")

    silent = config.get("silent")
    if silent is not None and not isinstance(silent, bool):
        raise ValueError(f"'silent' must be a boolean in {path}")

    dry_run = config.get("dry_run")
    if dry_run is not None and not isinstance(dry_run, bool):
        raise ValueError(f"'dry_run' must be a boolean in {path}")

    notify = config.get("notify")
    if notify is not None and not isinstance(notify, bool):
        raise ValueError(f"'notify' must be a boolean in {path}")

    notifications = config.get("notifications")
    if notifications is not None and not isinstance(notifications, bool):
        raise ValueError(f"'notifications' must be a boolean in {path}")

    log_file = config.get("log_file")
    if log_file is not None and not isinstance(log_file, str):
        raise ValueError(f"'log_file' must be a string in {path}")

    organizer_log = config.get("organizer_log")
    if organizer_log is not None and not isinstance(organizer_log, str):
        raise ValueError(f"'organizer_log' must be a string in {path}")
