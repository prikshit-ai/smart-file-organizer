"""
notifier.py - Cross-platform desktop notifications using plyer.
Silently degrades if plyer is not installed.
"""

import logging

logger = logging.getLogger(__name__)

_PLYER_AVAILABLE = None


def _check_plyer() -> bool:
    global _PLYER_AVAILABLE
    if _PLYER_AVAILABLE is None:
        try:
            import plyer  # noqa: F401
            _PLYER_AVAILABLE = True
        except ImportError:
            _PLYER_AVAILABLE = False
            logger.debug("plyer not installed — desktop notifications disabled.")
    return _PLYER_AVAILABLE


def notify(title: str, message: str, timeout: int = 5):
    """
    Send a desktop notification.

    Args:
        title: Notification title
        message: Notification body text
        timeout: Display duration in seconds
    """
    if not _check_plyer():
        return
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="Smart File Organizer",
            timeout=timeout,
        )
    except Exception as e:
        # Notifications are non-critical — never crash the main process
        logger.warning("Desktop notification failed (%s): %s", type(e).__name__, e)
