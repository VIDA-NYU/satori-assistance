import asyncio
import time
import base64
import requests
import httpx
import openai
import cv2
import numpy as np

from PIL import Image
from ...config import read_config
from ...pipeline.base import BasePipeline
from ...codec import JsonCodec, HoloframeCodec, BytesCodec
from ...stream import StreamConfig


class FramePipeline(BasePipeline):
    """
    A pipeline for buffering and concatenating image frames for downstream processing.

    Attributes:
        buffer_limit (int): Max number of frames to hold before concatenation
        dropout (int): Frame skipping interval (e.g., every 10th frame)
        image_stream_name (str): Stream name to match image source
    """

    def __init__(self, 
                 stream_map = {},
                 buffer_limit=3, downsample_rate=3, postprocess=None, image_stream_name="main"):
        super().__init__(stream_map=stream_map)
        self.concat_image = None
        self.concat_image_set = False
        self.buffer = []
        self.stored_frames = []
        self.buffer_limit = buffer_limit
        self.downsample_rate = downsample_rate
        self.index = 0
        self.enabled = False
        self.busy = False
        self.image_stream_name = image_stream_name
        self.add_input_stream(
            StreamConfig('main', HoloframeCodec)
        )

    async def on_image_input_stream(self, message):
        """
        Called when a new image is received. Decides whether to buffer and concatenate.
        """
        if self.index % self.downsample_rate == 0:
            image_rgb = cv2.cvtColor(message['image'], cv2.COLOR_BGR2RGB)
            self.buffer.append(image_rgb)
            self.index = 0
        self.index += 1
        if len(self.buffer) >= self.buffer_limit:
            long_picture = np.concatenate(self.buffer, axis=1)
            self.concat_image = long_picture
            self.concat_image_set = True
            self.stored_frames.extend(self.buffer)
            self.buffer = self.buffer[1:]  # drop oldest

    async def check_and_process_image_stream(self, message, sid):
        """
        Validates if the input is from the designated image stream, and if so, processes it.
        """
        if sid == self.image_stream_name and message is not None and not self.busy:
            await self.on_image_input_stream(message)
            return True
        return False

    async def on_input_stream(self, message, sid):
        """
        Entry point for stream data. Currently handles image data.
        """
        await self.check_and_process_image_stream(message, sid)
        return {}

    async def get_frames(self, k=3):
        """
        Returns the last k frames including from the buffer and stored frames.
        """
        n_store_needed = k - len(self.buffer)
        return self.stored_frames[-n_store_needed:] + self.buffer

    async def get_concat_image(self, resize_ratio=0.3):
        """
        Returns the resized concatenated image if available.
        """
        if self.concat_image_set:
            try:
                resized = cv2.resize(self.concat_image, (0, 0), fx=resize_ratio, fy=resize_ratio)
                return True, resized
            except Exception as e:
                print("Error during resizing:", e)
                self.busy = False
                return False, None
        return False, None


def configure_openai(api_key):
    """
    Sets the OpenAI API key securely.
    """
    openai.api_key = api_key
    openai.verify_ssl_certs = False
