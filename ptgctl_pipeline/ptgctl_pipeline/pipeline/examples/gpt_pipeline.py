import asyncio
import openai
from ..base import BasePipeline


def configure_openai(api_key: str):
    openai.api_key = api_key
    openai.verify_ssl_certs = False


class GPTPipeline(BasePipeline):
    """
    A simple GPT-based pipeline that uses a text-only prompt to generate responses.

    Args:
        prompt_message (str): The system prompt used for the GPT model.
        input_stream_name (str): Name of the stream to listen for input.
        output_stream_name (str): Stream to output the GPT response.
        sleep_time (int): Optional delay to simulate async waiting.
        preprocess (Callable): Optional preprocessing function on the message.
    """

    def __init__(self, prompt_message: str, input_stream_name: str, output_stream_name: str,
                 sleep_time: int = 1, preprocess=None):
        super().__init__([], [input_stream_name], [output_stream_name])
        self.prompt_message = prompt_message
        self.sleep_time = sleep_time
        self.preprocess = preprocess

    async def on_input_stream(self, buffer):
        """Handles incoming input messages (text)."""
        message = buffer.decode("utf-8")
        await asyncio.sleep(self.sleep_time)
        print(f"[Input] {message}")

    async def on_trigger_stream(self, message):
        """Uses GPT to respond to a trigger message."""
        if self.preprocess:
            message = self.preprocess(message)

        messages = [
            {"role": "system", "content": self.prompt_message},
            {"role": "user", "content": message}
        ]

        success, result = self.fetch_gpt_response(messages)
        return result if success else "[Error] GPT request failed."

    def fetch_gpt_response(self, messages, gpt_model="gpt-4"):
        """Queries OpenAI GPT model with chat messages."""
        try:
            completion = openai.ChatCompletion.create(
                model=gpt_model,
                messages=messages,
                max_tokens=4096
            )
            content = completion["choices"][0]["message"]["content"]
            return True, content
        except Exception as e:
            print(f"[GPT Error] {e}")
            return False, "Failed to fetch the data."
