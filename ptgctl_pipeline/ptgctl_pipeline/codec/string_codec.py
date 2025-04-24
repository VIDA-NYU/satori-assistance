from .base import BaseCodec


class StringCodec(BaseCodec):
    """
    Codec for UTF-8 string encoding and decoding.

    Converts between Python strings and UTF-8 encoded byte strings.
    """

    @classmethod
    def encode(cls, data):
        """
        Encode a string into UTF-8 bytes.

        Args:
            data (str): Input string to encode.

        Returns:
            bytes: UTF-8 encoded byte string.
        """
        return data.encode("utf-8")

    @classmethod
    def decode(cls, data):
        """
        Decode UTF-8 bytes into a string.

        Args:
            data (bytes): UTF-8 encoded byte string.

        Returns:
            str: Decoded string.
        """
        return data.decode("utf-8")
