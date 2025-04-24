import asyncio
import time
from ..base import BasePipeline


class PrintPipeline(BasePipeline):
    """
    A simple debugging pipeline that prints messages from input and trigger streams.

    Args:
        input_stream_name (str): Stream to treat as a trigger
        output_stream_name (str): Output stream to send processed response
        sleep_time (int): Optional delay to simulate processing latency (seconds)
    """

    def __init__(self, input_stream_name: str, output_stream_name: str, sleep_time: int = 1):
        super().__init__([], [input_stream_name], [output_stream_name])
        self.sleep_time = sleep_time

    async def on_input_stream(self, buffer, sid):
        """Prints a decoded input message after a delay."""
        message = buffer.decode("utf-8")
        await asyncio.sleep(self.sleep_time)
        print(f"[Input:{sid}] {message}")

    async def on_trigger_stream(self, buffer):
        """Prints a trigger message and returns a response after a delay."""
        message = buffer
        print(f"[Trigger] {message}")
        await asyncio.sleep(self.sleep_time)
        result = f"Print: {message}"
        print(f"[Output] {result}")
        return result
