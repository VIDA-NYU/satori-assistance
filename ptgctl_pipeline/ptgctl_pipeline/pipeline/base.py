import asyncio
from ..stream import StreamConfig
from ..codec import StringCodec

class BasePipeline:
    """
    Base class for stream-driven pipelines in the Satori framework.

    This version supports role-based stream binding via input_streams (dict),
    trigger_streams (list of roles), and output_streams (list of roles).
    """

    def __init__(self, *,  stream_map = {}, context=None, name=None, output_mode="single"):
        self.name = name or self.__class__.__name__
        self.context = context
        self.output_mode = output_mode

        # self.roles = input_streams  # {role: sid}
        self.sid_index = {}

        self.stream_map = stream_map

        # Initialize streams
        self.input_streams = []
        self.trigger_streams = []
        self.output_streams = []

        self.reverse_stream_map = {}
        for k, v in stream_map.items():
            self.reverse_stream_map[v] = k
        # self.roles = {**input_role_stream_map, **trigger_role_stream_map, **output_role_stream_map}
        # self.role_to_sid = lambda x: self.roles[x].sid
        # self.sid_to_role = {v: k for k, v in self.role_to_sid.items()}
        # print(self.input_streams)


    def _init_streams(self, stream_map):
        """Initialize input streams from a role→stream ID dict."""
        result = {}
        role_strema_map = {}
        streams = []
        if isinstance(stream_map, list):
            for stream in stream_map:
                stream = self._validate_stream(stream)
                self.sid_index[stream.sid] = stream
                streams.append(stream)
                role_strema_map[stream.sid] = stream
            return streams, role_strema_map
        if isinstance(stream_map, dict):
            for role, stream in stream_map.items():
                stream = self._validate_stream(stream)
                self.sid_index[stream.sid] = stream
                streams.append(stream)
                role_strema_map[stream.sid] = stream
            return streams, role_strema_map
        raise ValueError("Input streams must be a list or dict")

    def _init_stream_list(self, roles_or_sids):
        """Initialize trigger/output streams from role names or raw sids."""
        result = []
        for r in roles_or_sids:
            sid = self.get_stream(r)
            stream = self._validate_stream(sid)
            result.append(stream)
            self.sid_index[stream.sid] = stream
        return result

    @staticmethod
    def _validate_stream(stream_config):
        if isinstance(stream_config, str):
            return StreamConfig(sid=stream_config, codec=StringCodec)
        elif isinstance(stream_config, StreamConfig):
            return stream_config
        raise ValueError("Stream must be a string or StreamConfig instance")

    def add_input_stream(self, stream_config):
        stream_config = self._validate_stream(stream_config)
        self.input_streams.append(stream_config)
        self.sid_index[stream_config.sid] = stream_config

    def add_trigger_stream(self, stream_config):
        stream_config = self._validate_stream(stream_config)
        self.trigger_streams.append(stream_config)
        self.sid_index[stream_config.sid] = stream_config
   
    def add_output_stream(self, stream_config):
        stream_config = self._validate_stream(stream_config)
        self.output_streams.append(stream_config)
        self.sid_index[stream_config.sid] = stream_config

    def add_input_streams(self, streams):
        for stream in streams:
            self.add_input_stream(stream)

    def add_trigger_streams(self, streams):
        for stream in streams:
            self.add_trigger_stream(stream)
    
    def add_output_streams(self, streams):
        for stream in streams:
            self.add_output_stream(stream)

    def get_stream(self, role):
        if role not in self.roles:
            raise ValueError(f"Missing stream role: {role}")
        return self.roles[role]
    
    def get_input_streams(self):
        return self.input_streams
    
    def get_trigger_streams(self):
        return self.trigger_streams

    def get_output_streams(self):
        return self.output_streams

    def get_input_stream_names(self):
        # return [s.sid for s in self.input_streams]
        return [self.stream_map.get(s.sid, s.sid) for s in self.input_streams]

    def get_trigger_stream_names(self):
        return [self.stream_map.get(s.sid, s.sid) for s in self.trigger_streams]

    def get_output_stream_names(self):
        return [self.stream_map.get(s.sid, s.sid) for s in self.output_streams]

    def is_multi_output(self):
        return len(self.output_streams) > 1

    def get_server_side_stream_id(self, sid):
        return self.stream_map.get(sid, sid)

    def get_internal_sid(self, sid):
        return self.reverse_stream_map.get(sid, sid)
    
    async def handle_input_stream(self, message, sid):
        internal_sid = self.reverse_stream_map.get(sid, sid)
        await self.on_input_stream(message, internal_sid)

    async def handle_trigger_stream(self, message, sid):
        internal_sid = self.reverse_stream_map.get(sid, sid)
        return await self.on_trigger_stream(message, internal_sid)
    
    async def on_input_stream(self, message, sid):
        raise NotImplementedError("on_input_stream not implemented")

    async def on_trigger_stream(self, message):
        raise NotImplementedError("on_trigger_stream not implemented")

    async def handle_input(self, message, sid):
        decoded = self.decode_stream_data(sid, message)
        await self.on_input_stream(decoded, sid)

    async def handle_trigger(self, message):
        decoded = self.decode_stream_data(self.trigger_streams[0].sid, message)
        await self.on_trigger_stream(decoded)

    def decode_stream_data(self, sid, data):
        return self.sid_index[sid].codec.decode(data)

    def encode_stream_data(self, sid, data):
        return self.sid_index[sid].codec.encode(data)

    def write_output(self, sid, data):
        encoded = self.encode_stream_data(sid, data)
        return encoded  # Placeholder for actual stream write logic

    def on_registering_pipeline(self, context):
        self.context = context

    def get_context(self):
        return self.context

    # Logging
    def _log(self, level, *messages, **extra):
        if self.context is None:
            return
        msg = " ".join(str(m) for m in messages)
        log_fn = getattr(self.context, level, None)
        if callable(log_fn):
            return log_fn(msg, self.name, **extra)

    def debug(self, *msg, **extra):
        return self._log("debug", *msg, **extra)

    def info(self, *msg, **extra):
        return self._log("info", *msg, **extra)

    def warning(self, *msg, **extra):
        return self._log("warning", *msg, **extra)

    def error(self, *msg, **extra):
        return self._log("error", *msg, **extra)

    def critical(self, *msg, **extra):
        return self._log("critical", *msg, **extra)
