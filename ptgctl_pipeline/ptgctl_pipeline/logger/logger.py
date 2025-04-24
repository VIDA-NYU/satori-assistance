from typing import List
from .types import TimeFormatter, LogLevel, LogMessage
from .handlers import LogHandler, ConsoleLogHandler, FileLogHandler, JSONLogHandler


class Logger:
    """
    A flexible logger that supports multiple output handlers and log levels.

    Supports structured logging with metadata, level filtering, and dispatching
    to console, file, or JSON-based outputs.
    """

    def __init__(self):
        self.handlers: List[LogHandler] = []
        self.min_level = LogLevel.DEBUG  # Default log level

    def add_handler(self, handler: LogHandler) -> 'Logger':
        """
        Add a new handler to emit log messages to.

        Args:
            handler (LogHandler): A log handler instance (e.g., ConsoleLogHandler)
        Returns:
            Logger: self for method chaining
        """
        self.handlers.append(handler)
        return self

    def set_level(self, level: LogLevel) -> 'Logger':
        """
        Set the minimum level of logs to emit.

        Args:
            level (LogLevel): Minimum severity level
        Returns:
            Logger: self for method chaining
        """
        self.min_level = level
        return self

    def log(self, level: LogLevel, message: str, sender: str, **extra):
        """
        Emit a log message if it meets the minimum severity.

        Args:
            level (LogLevel): Severity level
            message (str): Log message body
            sender (str): Name of the component or module emitting the log
            extra (dict): Additional metadata
        """
        if level.value >= self.min_level.value:
            log_message = LogMessage(level, message, sender, extra=extra)
            for handler in self.handlers:
                handler.emit(log_message)

    # Convenience wrappers for common log levels
    def debug(self, message: str, sender: str, **extra):
        return self.log(LogLevel.DEBUG, message, sender, **extra)

    def info(self, message: str, sender: str, **extra):
        return self.log(LogLevel.INFO, message, sender, **extra)

    def warning(self, message: str, sender: str, **extra):
        return self.log(LogLevel.WARNING, message, sender, **extra)

    def error(self, message: str, sender: str, **extra):
        return self.log(LogLevel.ERROR, message, sender, **extra)

    def critical(self, message: str, sender: str, **extra):
        return self.log(LogLevel.CRITICAL, message, sender, **extra)
