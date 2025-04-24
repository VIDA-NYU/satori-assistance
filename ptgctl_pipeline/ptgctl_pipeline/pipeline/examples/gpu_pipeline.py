import cv2
import openai
import base64
import asyncio
import requests
import numpy as np
from PIL import Image

from ptgctl_pipeline.config import read_config
from ptgctl_pipeline.pipeline.base import BasePipeline
from ptgctl_pipeline.codec import JsonCodec, HoloframeCodec, BytesCodec
from ptgctl_pipeline.stream import StreamConfig


def configure_openai(api_key: str):
    """Configure OpenAI API key and SSL settings."""
    openai.api_key = api_key
    openai.verify_ssl_certs = False


class GPUPipeline(BasePipeline):
    """
    A pipeline example utilizing GPU resources.

    Args:
        input_streams (list[str] | list[StreamConfig]): Input stream configs or names
        trigger_streams (list[str] | list[StreamConfig]): Trigger stream configs or names
        output_streams (list[str] | list[StreamConfig]): Output stream configs or names
        device (str): GPU device name or index (e.g., 'cuda:0')
    """

    def __init__(self, input_streams, trigger_streams, output_streams, device):
        super().__init__(input_streams, trigger_streams, output_streams)
        self.device = device

    # Override this method in subclasses
    async def on_input_stream(self, message, sid):
        pass

    # Override this method in subclasses
    async def on_trigger_stream(self, message):
        pass