from .base import BaseCodec


class BytesCodec(BaseCodec):
    """
    A pass-through codec that returns data unchanged.

    This is useful for raw byte streams or when encoding/decoding is unnecessary.
    """

    @classmethod
    def encode(cls, data):
        """
        Return the data unchanged.

        Args:
            data (Any): Input data.

        Returns:
            Any: Same as input.
        """
        return data

    @classmethod
    def decode(cls, data):
        """
        Return the data unchanged.

        Args:
            data (Any): Encoded data.

        Returns:
            Any: Same as input.
        """
        return data
