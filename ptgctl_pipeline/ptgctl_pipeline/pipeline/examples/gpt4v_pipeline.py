import time
import base64
import asyncio
import requests
import httpx
import openai
import cv2
import numpy as np
from pydantic import BaseModel

from .frame_pipeline import FramePipeline

import os

env_openai_key = os.getenv("OPENAI_API_KEY")

def configure_openai(api_key):
    openai.api_key = api_key
    openai.verify_ssl_certs = False


def assemble_headers(api_key):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }


def bytes_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')


def assemble_gpt4v_request(image_bytes, system_prompt, prompt_text):
    return {
        "model": "gpt-4o-2024-08-06",
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{bytes_to_base64(image_bytes)}"}}
                ]
            }
        ]
    }


def query_gpt4v(image_bytes, system_prompt, prompt_text, api_key):
    payload = assemble_gpt4v_request(image_bytes, system_prompt, prompt_text)
    headers = assemble_headers(api_key)
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']


async def query_gpt4v_async(image_bytes, system_prompt, prompt_text, api_key):
    payload = assemble_gpt4v_request(image_bytes, system_prompt, prompt_text)
    headers = assemble_headers(api_key)
    timeout = httpx.Timeout(60.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content']


class Response(BaseModel):
    type: str = "json_object"
    prompt_confirmation: bool = True
    guidance_flag: bool = True
    chat_flag: bool = False
    placeholder: bool = False
    chat_message_flag: bool = True
    chat_message: str = ""
    intent: str = ""
    desire_confirmation: str = ""
    desire: str = ""
    meta_intent: str = ""
    guidance_type: str = ""
    confirmation_content: str = ""
    lod: str = ""
    text_guidance_title: str = ""
    text_guidance_content: str = ""
    prompt: str = ""
    highlight_object_flag: bool = False
    highlight_object_loc: str = "none"
    highlight_object_label: str = "N/A"


class GPT4VPipeline(FramePipeline):
    def __init__(self,
                 system_prompt,
                 api_key = "",
                 buffer_limit=4,
                 downsample_rate=3,
                 postprocess=None,
                 stream_map = {},
                 ):
        super().__init__(
            buffer_limit = buffer_limit, 
            downsample_rate=downsample_rate,
            postprocess = postprocess,
            stream_map = stream_map, 
        )       
        self.system_prompt = system_prompt
        self.api_key = api_key or env_openai_key
        self.postprocess = postprocess

    async def on_input_stream(self, message, sid):
        if self.busy:
            return
        await self.check_and_process_image_stream(message, sid)
        return {}

    async def on_image_input_stream(self, message):
        if self.index % self.downsample_rate == 0:
            image_rgb = cv2.cvtColor(message['image'], cv2.COLOR_BGR2RGB)
            self.buffer.append(image_rgb)
            self.index = 0
        self.index += 1

        if len(self.buffer) >= self.buffer_limit:
            self.concat_image = np.concatenate(self.buffer, axis=1)
            self.concat_image_set = True
            self.buffer = []

    async def on_trigger_stream(self, message):
        self.busy = True
        if self.concat_image_set:
            try:
                resized_image = cv2.resize(self.concat_image, (0, 0), fx=0.1, fy=0.1)
                response = await self.fetch_gpt_response_async(resized_image)
                if self.postprocess:
                    response = self.postprocess(response['result'])
                return response
            finally:
                self.busy = False
        self.busy = False

    async def fetch_gpt_response_async(self, image, prompt_message=None, system_prompt=None):
        image_bytes = cv2.imencode('.png', image)[1].tobytes()
        prompt = prompt_message or self.get_prompt_message()
        system = system_prompt or self.system_prompt
        try:
            response = await query_gpt4v_async(image_bytes, system, prompt, self.api_key)
            result, thoughts = self.parse_result(response)
            return {"success": True, "response": response, "thoughts": thoughts, "result": result}
        except Exception as e:
            return {"success": False, "response": str(e)}

    def fetch_gpt_response(self, image):
        image_bytes = cv2.imencode('.png', image)[1].tobytes()
        try:
            response = query_gpt4v(image_bytes, self.system_prompt, self.get_prompt_message(), self.api_key)
            result, thoughts = self.parse_result(response)
            return {"success": True, "response": response, "thoughts": thoughts, "result": result}
        except Exception as e:
            return {"success": False, "response": str(e)}

    def get_prompt_message(self):
        raise NotImplementedError("Prompt message getter must be implemented by subclass.")

    def parse_result(self, response):
        lines = response.split("\n")
        thoughts, result = [], "No result"
        for line in lines:
            if line.startswith("#"):
                thoughts.append(line)
            else:
                result = line
        return result, "\n".join(thoughts)
