import json
from .base import BaseCodec


class JsonCodec(BaseCodec):
    """
    Codec for encoding and decoding JSON-serializable data.

    Encodes Python data structures into UTF-8 JSON bytes and decodes
    JSON byte strings back into Python objects.
    """

    @classmethod
    def encode(cls, buffer):
        """
        Encode Python object to UTF-8 encoded JSON bytes.

        Args:
            buffer (Any): A JSON-serializable Python object.

        Returns:
            bytes: UTF-8 encoded JSON.
        """
        return json.dumps(buffer).encode("utf-8")

    @classmethod
    def decode(cls, buffer):
        """
        Decode UTF-8 encoded JSON bytes into a Python object.

        Args:
            buffer (bytes): Encoded JSON byte string.

        Returns:
            Any: Decoded Python object.
        """
        return json.loads(buffer.decode("utf-8"))
