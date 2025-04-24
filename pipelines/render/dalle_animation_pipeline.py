"""
Dalle Animation Pipeline

Generates a multi-step instructional animation from a semicolon-separated prompt using OpenAI DALL-E.
"""

import asyncio
import aiohttp
import os
import httpx

from ptgctl_pipeline.ptgctl_pipeline.pipeline.base import BasePipeline
from ptgctl_pipeline.ptgctl_pipeline.stream import StreamConfig
from ptgctl_pipeline.ptgctl_pipeline.codec import JsonCodec, BytesCodec
from ptgctl_pipeline.ptgctl_pipeline.pipeline.examples.gpt4v_pipeline import assemble_headers
from .image_sequence_pb2 import ImageSequence


def format_protobuf_bytes(image_bytes_list, sequence_id, sequence_type, playing_interval=1.0):
    """
    Convert a list of image byte arrays to a serialized protobuf message.

    :param image_bytes_list: List of image content in bytes.
    :type image_bytes_list: list[bytes]
    :param sequence_id: Identifier for the animation sequence.
    :type sequence_id: int
    :param sequence_type: Type label for the image sequence.
    :type sequence_type: str
    :param playing_interval: Playback interval between images.
    :type playing_interval: float
    :return: Serialized protobuf message.
    :rtype: bytes
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

class DallePipelineAnim(BasePipeline):
    """
    Pipeline for generating instructional animation sequences using DALL-E prompts.

    .. note::
       This pipeline receives a semicolon-separated prompt, splits it into steps,
       and generates one frame per step.
    """

    INPUT_STREAM = "intent:intent"
    TRIGGER_STREAM = "assistant:summary"
    OUTPUT_STREAM = "chat:assistant:image"

    def __init__(self,
            api_key: str = "",
            stream_map = {},
        ):
        """Initialize the animation pipeline with stream configs and internal state."""
        super().__init__(
            stream_map=stream_map,
        )
        self.add_input_streams(
            [StreamConfig(self.INPUT_STREAM, JsonCodec)]
        )
        self.add_trigger_streams(
            [StreamConfig(self.TRIGGER_STREAM, JsonCodec)]
        )
        self.add_output_streams(
            [StreamConfig(self.OUTPUT_STREAM, BytesCodec)]
        )
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.index = 0
        self.state_data = {}
        self.state_data_initialized = False

    async def on_input_stream(self, message, sid):
        """
        Handle input stream message (no-op for now).

        :param message: Stream message payload.
        :param sid: Stream ID.
        """
        pass

    async def on_trigger_stream(self, data):
        """
        Handle trigger stream to generate animation frames.

        :param data: Dictionary with prompt and index metadata.
        :type data: dict
        :return: Byte stream of encoded image sequence.
        :rtype: bytes or None
        """
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
        """
        Convert a semicolon-separated prompt string into styled individual prompts.

        :param prompt: Prompt with steps separated by ";"
        :type prompt: str
        :return: List of stylized prompts for each frame.
        :rtype: list[str]
        """
        steps = prompt.split(";")
        modifier = " in the style of flat, instructional illustrations. no background. accurate, concise, comfortable color style"
        prefix = "I NEED to test how the tool works with extremely simple prompts. DO NOT add any detail, just use it AS-IS: "
        return [prefix + step[3:] + modifier for step in steps if step.strip()]

    async def generate_images(self, prompts):
        """
        Generate multiple image URLs by querying DALL-E.

        :param prompts: List of individual prompts.
        :type prompts: list[str]
        :return: List of image URLs.
        :rtype: list[str]
        """
        return await asyncio.gather(*[self.fetch_gpt_response(prompt) for prompt in prompts])

    async def fetch_gpt_response(self, prompt, gpt_model="dall-e-3"):
        """
        Fetch a single image URL from the OpenAI DALL-E API.

        :param prompt: The image generation prompt.
        :type prompt: str
        :param gpt_model: Name of the DALL-E model.
        :type gpt_model: str
        :return: Image URL string or None.
        :rtype: str or None
        """
        try:
            headers = assemble_headers(self.api_key)
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
        """
        Load a default image when generation fails.

        :return: Default image in bytes.
        :rtype: bytes
        """
        with open("static/loading.png", "rb") as f:
            return f.read()


async def download_image_async(url):
    """
    Download an image from a URL asynchronously.

    :param url: URL of the image.
    :type url: str
    :return: Image content in bytes.
    :rtype: bytes
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()
