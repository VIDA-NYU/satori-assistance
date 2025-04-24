from .base import BaseCodec
from ptgctl import holoframe


class HoloframeCodec(BaseCodec):
    """
    Codec for encoding and decoding data using ptgctl's holoframe format.

    This codec is suitable for structured sensor/frame data requiring
    serialization through the holoframe protocol.
    """

    @classmethod
    def encode(cls, value):
        """
        Encode data into holoframe v3 format.

        Args:
            value (Any): Structured input data.

        Returns:
            bytes: Encoded holoframe byte stream.
        """
        return holoframe.dump_v3(value)

    @classmethod
    def decode(cls, value: bytes):
        """
        Decode data from holoframe format.

        Args:
            value (bytes): Encoded byte stream.

        Returns:
            Any: Decoded structured data.
        """
        return holoframe.load(value)
