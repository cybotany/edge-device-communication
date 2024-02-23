from abc import ABC, abstractmethod
import logging

class NFC(ABC):
    """
    Abstract base class for NFC tags interaction through a PN532 NFC/RFID controller.

    This class defines a common interface for various NFC operations.

    Attributes:
        pn532 (PN532): Instance of PN532 class used for NFC communication.
        uid (str): Unique identifier for the NFC tag.
    """

    def __init__(self, pn532, uid):
        """
        Initializes the NFC with a PN532 instance.

        Args:
            pn532 (PN532): The PN532 instance used for NFC communication.
            uid (str): The unique identifier for the NFC tag.
        """
        self.pn532 = pn532
        self.uid = uid

    @property
    @abstractmethod
    def block_size(self):
        """
        Specifies the block size for the subclass.
        """
        pass

    def read_block(self, block_number):
        """
        Reads a block of data from the NFC tag.
        The method uses the `block_size` attribute to determine how many bytes to read.

        Args:
            block_number (int): The block/page number to read.

        Returns:
            list[int]: Data read from the specified block.
        """
        params = bytearray([0x01, self.read_cmd, block_number & 0xFF])
        response = self.pn532._call_function(params=params, response_length=self.block_size + 1)
        return response[1:][:self.block_size]

    def write_block(self, block_number, data):
        """
        Writes a block of data to the NFC tag.
        Validates that the data length matches the `block_size` before attempting to write.

        Args:
            block_number (int): The block number/page to write to.
            data (list[int]): The data to write to the block.
        
        Returns:
            bool: True if the write operation was successful, False otherwise.
        """
        assert data is not None and len(data) == self.block_size, f'Data must be an array of {self.block_size} bytes!'
        params = bytearray([0x01, self.write_cmd, block_number & 0xFF]) + bytearray(data)
        response = self.pn532._call_function(params=params, response_length=1)
        return response[0] == 0x00

    def log(self, message, level="info"):
        """
        Logs a message with the specified severity level.

        Args:
            message (str): The message to log.
            level (str): The severity level of the log ('info', 'warning', 'error').
        """
        if level == "info":
            logging.info(message)
        elif level == "warning":
            logging.warning(message)
        elif level == "error":
            logging.error(message)
