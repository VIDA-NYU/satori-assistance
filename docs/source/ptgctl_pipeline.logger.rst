Logger Module
=============

The `logger` module provides a lightweight, structured logging system for the Satori pipeline framework.
It supports multiple logging levels, customizable time formatting, and flexible output targets
including console, plain text files, and structured JSON files.

Components
----------

.. automodule:: ptgctl_pipeline.ptgctl_pipeline.logger.types
   :members:
   :undoc-members:
   :show-inheritance:
   :synopsis: Logging types and timestamp formatting

.. automodule:: ptgctl_pipeline.ptgctl_pipeline.logger.handlers
   :members:
   :undoc-members:
   :show-inheritance:
   :synopsis: Console, file, and JSON log output handlers

.. automodule:: ptgctl_pipeline.ptgctl_pipeline.logger
   :members:
   :undoc-members:
   :show-inheritance:
   :synopsis: Core logger interface for emitting log messages

How It Works
------------

- `Logger`: Main entry point. Supports level-based filtering and multiple log outputs.
- `LogHandler`: Base class for any output format. Subclass to customize where and how logs are written.
- `LogMessage`: Structured message object with metadata and ISO-formatted timestamps.
- `TimeFormatter`: Utility to convert UTC timestamps into human-readable or local time.
