import enum
import json
import pytz
import datetime
from dataclasses import dataclass, asdict, field
from typing import Any, Dict


class LogLevel(enum.Enum):
    """
    Enum representing log severity levels.
    """
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


@dataclass
class LogMessage:
    """
    Data structure representing a single log message.

    Attributes:
        level (LogLevel): Severity level.
        message (str): Main log message.
        sender (str): Component name generating the log.
        timestamp (datetime): Timestamp in UTC (default: now).
        extra (dict): Additional metadata.
    """
    level: LogLevel
    message: str
    sender: str
    timestamp: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(pytz.utc))
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the log message to a serializable dictionary.

        Returns:
            dict: Dictionary representation of the log message.
        """
        return {
            "sender": self.sender,
            "level": self.level.name,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            **self.extra
        }


class TimeFormatter:
    """
    Utility class for formatting log timestamps with timezone awareness.

    Args:
        format_string (str): Datetime format string.
        timezone (str): Timezone string compatible with pytz.
    """

    def __init__(self, format_string: str = "%Y-%m-%d %H:%M:%S", timezone: str = "UTC"):
        self.format_string = format_string
        self.timezone = pytz.timezone(timezone)

    def format(self, timestamp: datetime.datetime) -> str:
        """
        Format a datetime object according to the configured format and timezone.

        Args:
            timestamp (datetime): UTC datetime to format.

        Returns:
            str: Formatted timestamp string.
        """
        localized_time = timestamp.astimezone(self.timezone)
        return localized_time.strftime(self.format_string)
