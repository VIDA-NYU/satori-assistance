class StreamConfig:
    """
    Configuration object for a data stream in the pipeline system.

    Attributes:
        sid (str): The unique stream ID or name.
        codec (BaseCodec): The codec used to encode and decode data for this stream.
    """

    def __init__(self, sid: str, codec):
        """
        Initialize a StreamConfig instance.

        Args:
            sid (str): Stream identifier.
            codec (BaseCodec): Codec instance for encoding/decoding stream data.
        """
        self.sid = sid
        self.codec = codec
