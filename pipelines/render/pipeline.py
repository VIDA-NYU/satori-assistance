"""
DALL-E Rendering Pipelines

This module provides two rendering pipelines using OpenAI DALL-E for generating static and animated image sequences.
It includes: 
  - `DallePipeline`: renders a single image based on a prompt
  - `DallePipelineAnim`: renders a sequence of instructional frames based on step-by-step prompt input

Author: [Your Name]
"""

# === Standard Library ===
import time
import io
import asyncio
import requests
import numpy as np

# === Third-party Libraries ===
import httpx
import aiohttp
from PIL import Image

# === Internal Libraries ===
from ptgctl_pipeline.ptgctl_pipeline.pipeline.base import BasePipeline
from ptgctl_pipeline.ptgctl_pipeline.stream import StreamConfig
from ptgctl_pipeline.ptgctl_pipeline.codec import JsonCodec, BytesCodec
from ptgctl_pipeline.ptgctl_pipeline.pipeline.examples.gpt4v_pipeline import assemble_headers
from .image_sequence_pb2 import ImageSequence
from .image_cache import ImageCache
from logger_config import setup_logger

logger = setup_logger(__name__, "dalle_pipeline.log")


def format_protobuf_bytes(image_bytes_list, sequence_id, sequence_type, playing_interval=1.0):
    """
    Formats a list of image byte arrays into a serialized protobuf message.
    """
    sequence = ImageSequence()
    sequence.sequence_id = sequence_id
    sequence.sequence_type = sequence_type
    sequence.playing_interval = playing_interval
    for i, img in enumerate(image_bytes_list):
        image_data = sequence.images.add()
        image_data.content = img
        image_data.filename = f"image_{i}.png"
    return sequence.SerializeToString()


class DallePipeline(BasePipeline):
    """
    A pipeline that generates a single image from a text prompt using DALL-E.
    """
    INPUT_STREAM = "assistant:slow_activate"
    TRIGGER_STREAM = "assistant:summary"
    OUTPUT_STREAM = "chat:assistant:image"

    def __init__(self):
        super().__init__(
            [StreamConfig(self.INPUT_STREAM, JsonCodec)],
            [StreamConfig(self.TRIGGER_STREAM, JsonCodec)],
            [StreamConfig(self.OUTPUT_STREAM, BytesCodec)]
        )
        self.memory = ""
        self.index = 0
        self.state_data = {}
        self.state_data_initialized = False
        logger.info("Dalle Pipeline Initialized")

    async def on_input_stream(self, message, sid):
        pass

    async def on_trigger_stream(self, data):
        if data.get('guidance_type') != 'image':
            return None
        if self.state_data_initialized and self.state_data.get('index') == data.get('slow_index'):
            return None

        self.state_data['index'] = data.get('slow_index')
        self.state_data_initialized = True

        prompt = data.get("prompt")
        if not prompt:
            logger.error("Prompt not found")
            return self.load_default_image()

        if self.memory == prompt:
            return None

        self.index += 1
        self.memory = prompt

        modifier = " in the style of flat, instructional illustrations. no background. accurate, concise, comfortable color style"
        prefix = "I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS: "
        full_prompt = prefix + prompt + modifier
        logger.info(f"Prompt: {full_prompt}")

        flag, image_url = await self.fetch_gpt_response(full_prompt)
        if not flag:
            return self.load_default_image()

        image_data = self.download_image(image_url)
        with open(f"dalle_figs/dalle_image{self.index}.png", "wb") as f:
            f.write(image_data)

        return format_protobuf_bytes([image_data], self.state_data['index'], 'image')

    def load_default_image(self):
        with open("static/loading.png", "rb") as f:
            return f.read()

    def download_image(self, url):
        return requests.get(url).content

    async def fetch_gpt_response(self, prompt, gpt_model="dall-e-3"):
        try:
            headers = assemble_headers()
            timeout = httpx.Timeout(60.0, connect=30.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                payload = {
                    "model": gpt_model,
                    "prompt": prompt,
                    "size": "1024x1024",
                    "quality": "standard",
                    "n": 1,
                    "response_format": "url"
                }
                response = await client.post("https://api.openai.com/v1/images/generations", headers=headers, json=payload)
                image_url = response.json()['data'][0]['url']
                return True, image_url
        except Exception as e:
            logger.error(f"Failed to fetch image: {e}")
            return False, None


class DallePipelineAnim(BasePipeline):
    """
    A pipeline that generates an animation sequence from a step-by-step prompt using DALL-E.
    """
    INPUT_STREAM = "intent:intent"
    TRIGGER_STREAM = "assistant:summary"
    OUTPUT_STREAM = "chat:assistant:image"

    def __init__(self):
        super().__init__(
            [StreamConfig(self.INPUT_STREAM, JsonCodec)],
            [StreamConfig(self.TRIGGER_STREAM, JsonCodec)],
            [StreamConfig(self.OUTPUT_STREAM, BytesCodec)]
        )
        self.index = 0
        self.state_data = {}
        self.state_data_initialized = False
        self.image_cache = ImageCache()

    async def on_input_stream(self, message, sid):
        pass

    async def on_trigger_stream(self, data):
        if data.get('guidance_type') != 'image':
            return None
        if self.state_data_initialized and self.state_data.get('index') == data.get('index'):
            return None

        self.index += 1
        self.state_data = data
        prompt = data.get("prompt")
        if not prompt:
            return self.load_default_image()

        steps = self.generate_steps(prompt)
        image_urls = await self.generate_images(steps)
        image_bytes_list = await asyncio.gather(*[download_image_async(url) for url in image_urls])
        return format_protobuf_bytes(image_bytes_list, self.state_data['index'], 'animation')

    def generate_steps(self, prompt):
        steps = prompt.split(";")
        modifier = " in the style of flat, instructional illustrations. no background. accurate, concise, comfortable color style"
        prefix = "I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS: "
        return [prefix + step[3:] + modifier for step in steps if step.strip()]

    async def generate_images(self, prompts):
        return await asyncio.gather(*[self.fetch_gpt_response(prompt) for prompt in prompts])

    async def fetch_gpt_response(self, prompt, gpt_model="dall-e-3"):
        try:
            headers = assemble_headers()
            timeout = httpx.Timeout(60.0, connect=30.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                payload = {
                    "model": gpt_model,
                    "prompt": prompt,
                    "size": "1024x1024",
                    "quality": "standard",
                    "n": 1,
                    "response_format": "url"
                }
                response = await client.post("https://api.openai.com/v1/images/generations", headers=headers, json=payload)
                return response.json()['data'][0]['url']
        except Exception as e:
            logger.error(f"Failed to fetch animation step: {e}")
            return None

    def load_default_image(self):
        with open("static/loading.png", "rb") as f:
            return f.read()


async def download_image_async(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()
