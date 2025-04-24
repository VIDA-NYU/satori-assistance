import asyncio
import signal
import requests
import httpx
import ptgctl

from .config import PTG_PASSWORD, PTG_USERNAME, PTG_URL
from .logger import Logger, ConsoleLogHandler, TimeFormatter, JSONLogHandler
from .utils.request import ProcessManager
import traceback
import os

class PipelineServer:
    """
    Server class to manage multiple pipelines and stream data processing.
    
    Responsibilities:
    - Connect to ptgctl streams (input, trigger, output)
    - Route stream events to corresponding pipelines
    - Handle trigger execution and output result posting
    - Manage internal queue and lifecycle
    """

    def __init__(self, config):
        self.config = config
        self.pipelines = []
        
        self.api = ptgctl.API(
            username=config.username,
            password=config.password,
            url=config.url
        )
        self.url = config.url
        self.data_queue = asyncio.Queue()

        # Setup logger
        self.logger = Logger()
        formatter = TimeFormatter()
        self.logger.add_handler(ConsoleLogHandler(formatter))
        self.logger.add_handler(JSONLogHandler("log"))

        self.init_request()
        self.trigger_streams = {}
        self.trigger_interval = 1
        self.process_manager = ProcessManager(self.headers)

    def register_pipeline(self, pipeline):
        """Registers a pipeline to the server."""
        self.pipelines.append(pipeline)
        pipeline.on_registering_pipeline(self)

    def register_trigger(self, stream_name, interval=1):
        """Sets the trigger stream and polling interval."""
        self.trigger_streams[stream_name] = {
            'stream_name': stream_name,
            "interval": interval,
        }
        # self.trigger_stream = stream_name
        # self.trigger_interval = interval

    def init_request(self):
        """Initializes token-based headers for REST API usage."""
        r = requests.post(f'{self.url}/token', data={'username': 'test', 'password': 'test'})
        token = r.json()['access_token']
        self.headers = {"Authorization": "Bearer " + token}

    def build_pipeline_stream_index(self):
        """Indexes input/trigger streams to associated pipelines."""
        input_index, trigger_index = {}, {}
        for i, pipeline in enumerate(self.pipelines):
            for sid in pipeline.get_input_stream_names():
                input_index.setdefault(sid, []).append(i)
            for sid in pipeline.get_trigger_stream_names():
                trigger_index.setdefault(sid, []).append(i)
        return input_index, trigger_index

    async def producer(self):
        """Listens to input and trigger streams, routes to pipelines."""
        in_idx, trig_idx = self.build_pipeline_stream_index()
        sids = list(set(in_idx.keys()) | set(trig_idx.keys()))
        async with self.api.data_pull_connect(sids, ack=True) as ws:
            self.info("Start Listening...", "PipelineServer")
            while True:
                for sid, t, buffer in await ws.recv_data():
                    for i in in_idx.get(sid, []):
                        internal_sid = self.pipelines[i].get_internal_sid(sid)
                        data = self.pipelines[i].decode_stream_data(internal_sid, buffer)
                        await self.pipelines[i].on_input_stream(data, internal_sid)
                    for i in trig_idx.get(sid, []):
                        internal_sid = self.pipelines[i].get_internal_sid(sid)
                        await self.data_queue.put({"pipeline_index": i, "sid": internal_sid, "buffer": buffer})

    async def consumer(self):
        """Processes data from trigger queue asynchronously."""
        while True:
            data = await self.data_queue.get()
            asyncio.create_task(self.process_data(data))

    async def process_data(self, data):
        """Processes trigger data and pushes pipeline output."""
        pipeline = self.pipelines[data['pipeline_index']]
        decoded = pipeline.decode_stream_data(data['sid'], data['buffer'])
        # generate a random str to test
        result = await pipeline.on_trigger_stream(decoded)
        if result is None:
            return

        output_sids, encoded_list = [], []
        for out_stream in pipeline.get_output_streams():
            out_data = result.get(out_stream.sid) if pipeline.is_multi_output() else result
            # print(f"Output stream: {out_stream.sid}")
            if out_data is None:
                continue
            # print(f"HERE Output stream: {out_stream.sid}")
            # server_side_stream_id = pipeline.get_server_side_stream_id(out_stream.sid)
            output_sids.append(pipeline.get_server_side_stream_id(out_stream.sid))
            encoded_list.append(pipeline.encode_stream_data(out_stream.sid, out_data))
            # print("server-side:", pipeline.get_server_side_stream_id(out_stream.sid))

        await self.connect_with_retries(output_sids, encoded_list, result)

    async def connect_with_retries(self, sids, encoded_list, result, retries=3, delay=2):
        """Retries connection to push output data with exponential backoff."""
        for attempt in range(retries):
            try:
                await self.send_request(sids, encoded_list)
                return
            except asyncio.TimeoutError as e:
                self.debug(f"Timeout: {e}", "connect_with_retries")
            except Exception as e:
                self.debug(f"Error: {e}", "connect_with_retries")
            await asyncio.sleep(delay)
            delay *= 2
        self.warning("All retry attempts failed.", "connect_with_retries")

    async def send_request(self, sids, buffers):
        """Sends output stream data to ptgctl server."""
        for sid, buf in zip(sids, buffers):
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(f"{self.url}/data/{sid}", files={'entries': buf}, headers=self.headers)
            except Exception as e:
                self.debug(f"HTTP send failed: {e} {sid} {self.url}\n {traceback.format_exc()}", "send_request")

    def start_process_manager(self):
        """Starts background trigger process via REST."""
        if not self.trigger_streams:
            self.warning("No trigger stream set.", "ProcessManager")
            return
        signal.signal(signal.SIGINT, self.process_manager.signal_handler)
        for trigger_stream in self.trigger_streams:
            self.process_manager.start_process(f"{self.url}/data/{trigger_stream}", self.trigger_streams[trigger_stream]['interval'])

    async def start(self):
        """Starts the pipeline server (producer + consumer)."""
        self.start_process_manager()
        await asyncio.gather(self.producer(), self.consumer())

    # Logging wrappers
    def debug(self, message, sender, **extra):
        return self.logger.debug(message, sender, **extra)

    def info(self, message, sender, **extra):
        return self.logger.info(message, sender, **extra)

    def warning(self, message, sender, **extra):
        return self.logger.warning(message, sender, **extra)

    def error(self, message, sender, **extra):
        return self.logger.error(message, sender, **extra)

    def critical(self, message, sender, **extra):
        return self.logger.critical(message, sender, **extra)


async def main():
    pass  # Placeholder for standalone testing

if __name__ == "__main__":
    asyncio.run(main())
