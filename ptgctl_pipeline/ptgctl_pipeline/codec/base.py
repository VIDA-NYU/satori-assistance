from abc import ABC, abstractmethod


class BaseCodec(ABC):
    """
    Abstract base class for encoding and decoding stream data.

    Subclasses must implement `encode` and `decode` class methods to define
    how stream data should be serialized and deserialized.
    """

    @classmethod
    @abstractmethod
    def encode(cls, data):
        """
        Encode the given data into bytes or a serializable format.

        Args:
            data (Any): The raw input data to encode.

        Returns:
            Any: Encoded representation suitable for transmission or storage.
        """
        pass

    @classmethod
    @abstractmethod
    def decode(cls, data):
        """
        Decode the input data back into its original format.

        Args:
            data (Any): Encoded data received from a stream.

        Returns:
            Any: Decoded original data.
        """
        pass
