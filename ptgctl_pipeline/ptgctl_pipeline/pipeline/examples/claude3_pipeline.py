import time
import base64
import requests
import cv2
import numpy as np
from ..base import BasePipeline


# ----------------------
# API Configuration
# ----------------------
ANTHROPIC_API_KEY = ""  # Move to secure config in production


def bytes_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")


def assemble_headers():
    return {
        "content-type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "messages-2023-12-15"
    }


def assemble_claude_request(image_bytes, system_prompt, prompt_text):
    image_base64 = bytes_to_base64(image_bytes)
    return {
        "model": "claude-3-opus-20240229",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}},
                    {"type": "text", "text": prompt_text},
                ]
            }
        ]
    }


def query_claude(image_bytes, system_prompt, prompt_text):
    start = time.time()
    payload = assemble_claude_request(image_bytes, system_prompt, prompt_text)
    headers = assemble_headers()
    response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
    result = response.json()
    print("[Claude3] Time taken:", time.time() - start)
    return result["content"][0]["text"]


# ----------------------
# Claude3 Pipeline
# ----------------------
class Claude3Pipeline(BasePipeline):
    def __init__(self, prompt_message, input_image_stream_name, trigger_stream_name,
                 output_stream_name, buffer_limit=4, dropout=30, postprocess=None):
        super().__init__(input_image_stream_name, trigger_stream_name, output_stream_name)
        self.system_prompt = prompt_message
        self.concat_image = None
        self.concat_image_set = False
        self.buffer = []
        self.buffer_limit = buffer_limit
        self.dropout = dropout
        self.index = 0
        self.enabled = False
        self.postprocess = postprocess

    async def on_input_stream(self, message, sid):
        self.index += 1
        if self.index % self.dropout == 0:
            image_rgb = cv2.cvtColor(message["image"], cv2.COLOR_BGR2RGB)
            self.buffer.append(image_rgb)
            self.index = 0

        if len(self.buffer) >= self.buffer_limit:
            self.concat_image = np.concatenate(self.buffer, axis=1)
            cv2.imwrite("long_picture.jpg", self.concat_image)
            self.concat_image_set = True
            self.buffer = []
        return {}

    async def on_trigger_stream(self, message):
        self.enabled = True
        if self.concat_image_set:
            result = self.fetch_gpt_response(self.concat_image)
            self.enabled = False
            if self.postprocess:
                result = self.postprocess(result)
            return result
        self.enabled = False

    def fetch_gpt_response(self, long_picture):
        try:
            image_bytes = cv2.imencode(".jpeg", long_picture)[1].tobytes()
            response = query_claude(image_bytes, self.system_prompt, self.system_prompt)
            result, thoughts = self.parse_result(response)
            return {"success": True, "response": response, "thoughts": thoughts, "result": result}
        except Exception as e:
            print(f"[Claude3 Error] {e}")
            return {"success": False, "response": "Failed to fetch the data."}

    def parse_result(self, result):
        lines = result.split("\n")
        thoughts, final_result = [], "No result available"
        for line in lines:
            if line.startswith("#"):
                thoughts.append(line)
            else:
                final_result = line
        return final_result, "\n".join(thoughts)
