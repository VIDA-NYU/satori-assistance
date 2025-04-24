import os
import json
from datetime import datetime
from .types import TimeFormatter, LogLevel, LogMessage


class LogHandler:
    """
    Abstract base class for all log handlers.
    Subclasses must implement the `emit` method.
    """
    def emit(self, log_message: LogMessage):
        raise NotImplementedError("Subclasses must implement emit method")


class ConsoleLogHandler(LogHandler):
    """
    Logs messages to the console with time formatting.
    """
    def __init__(self, time_formatter: TimeFormatter):
        self.time_formatter = time_formatter

    def emit(self, log_message: LogMessage):
        formatted_time = self.time_formatter.format(log_message.timestamp)
        print(f"[{formatted_time}] {log_message.level.name} {log_message.sender}: {log_message.message}")


class FileLogHandler(LogHandler):
    """
    Logs messages to a plain text file.
    """
    def __init__(self, filename: str, time_formatter: TimeFormatter):
        self.filename = filename
        self.time_formatter = time_formatter

    def emit(self, log_message: LogMessage):
        formatted_time = self.time_formatter.format(log_message.timestamp)
        formatted_message = f"{formatted_time} - {log_message.level.name} - {log_message.message}"
        with open(self.filename, 'a') as f:
            f.write(formatted_message + '\n')


class JSONLogHandler(LogHandler):
    """
    Logs messages to a JSON file, appending new messages as structured entries.
    """
    def __init__(self, filename_prefix: str, log_dir: str = "./logs"):
        os.makedirs(log_dir, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = os.path.join(log_dir, f"{filename_prefix}_{timestamp_str}.json")
        self.messages = []
        with open(self.filename, "w") as fp:
            json.dump({"messages": self.messages}, fp, indent=2)

    def emit(self, log_message: LogMessage):
        self.messages.append(log_message.to_dict())
        with open(self.filename, "w") as fp:
            json.dump({"messages": self.messages}, fp, indent=2)
