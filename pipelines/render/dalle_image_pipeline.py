"""
Dalle Image Pipeline

Generates a single instructional-style image using OpenAI's DALL-E based on a natural language prompt.
"""
import os
import requests
import httpx
from PIL import Image

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
    :param sequence_id: Identifier for the image sequence.
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

class DallePipeline(BasePipeline):
    """
    Pipeline for generating a single instructional image using DALL-E based on a prompt.
    """

    INPUT_STREAM = "assistant:slow_activate"
    TRIGGER_STREAM = "assistant:summary"
    OUTPUT_STREAM = "chat:assistant:image"

    def __init__(self,
        api_key: str = "",
        stream_map = {},
    ):
        """Initialize the image pipeline with stream configs and internal state."""
        super().__init__(
            # [StreamConfig(self.INPUT_STREAM, JsonCodec)],
            # [StreamConfig(self.TRIGGER_STREAM, JsonCodec)],
            # [StreamConfig(self.OUTPUT_STREAM, BytesCodec)]
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
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.memory = ""
        self.index = 0
        self.state_data = {}
        self.state_data_initialized = False
        logger.info("Dalle Pipeline Initialized")

    async def on_input_stream(self, message, sid):
        """
        Handle input stream message (no-op for now).

        :param message: Stream message payload.
        :param sid: Stream ID.
        """
        pass

    async def on_trigger_stream(self, data):
        """
        Handle trigger stream to generate an image.

        :param data: Dictionary with prompt and index metadata.
        :type data: dict
        :return: Serialized protobuf image data.
        :rtype: bytes or None
        """
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
        """
        Load a default image when generation fails.

        :return: Default image content.
        :rtype: bytes
        """
        with open("static/loading.png", "rb") as f:
            return f.read()

    def download_image(self, url):
        """
        Download an image from the provided URL.

        :param url: Image URL.
        :type url: str
        :return: Image content.
        :rtype: bytes
        """
        return requests.get(url).content

    async def fetch_gpt_response(self, prompt, gpt_model="dall-e-3"):
        """
        Fetch image URL from DALL-E API for the given prompt.

        :param prompt: The image generation prompt.
        :type prompt: str
        :param gpt_model: Name of the DALL-E model.
        :type gpt_model: str
        :return: Tuple of success flag and image URL.
        :rtype: tuple[bool, str or None]
        """
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
