"""ptgctl_pipeline

The ptgctl_pipeline package provides a framework for building modular stream-based
pipelines using ptgctl. It includes logger setup, server entrypoint, and utility
modules for encoding, streaming, and configuration.
"""

# from ptgctl_pipeline.ptgctl_pipeline.logger import Logger

from .entrypoint import PipelineServer
from .stream import StreamConfig


__all__ = ['PipelineServer', 'StreamConfig']

# __version__ = "0.1.0"