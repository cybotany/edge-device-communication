from abc import ABC, abstractmethod
import logging

class AbstractNTAG(ABC):
    """
    Abstract base class for NTAG NFC tags interaction through a PN532 NFC/RFID controller.

    This class defines a common interface for various NTAG operations, including reading and writing
    blocks, handling NDEF messages, and setting lock bits. Subclasses should provide concrete
    implementations for these operations.

    Attributes:
        pn532 (PN532): Instance of PN532 class used for NFC communication.
    """

    def __init__(self, pn532):
        """
        Initializes the AbstractNTAG with a PN532 instance.

        Args:
            pn532 (PN532): The PN532 instance used for NFC communication.
        """
        self.pn532 = pn532

    @abstractmethod
    def read_block(self, block_number):
        """
        Abstract method to read a single block from the NTAG.

        Args:
            block_number (int): The block number to read.

        Returns:
            list[int]: Data read from the specified block.

        Raises:
            NotImplementedError: When the subclass does not implement this method.
        """
        raise NotImplementedError("Subclass must implement read_block method.")

    @abstractmethod
    def write_block(self, block_number, data):
        """
        Abstract method to write data to a single block in the NTAG.

        Args:
            block_number (int): The block number to write to.
            data (list[int]): The data to write to the block.

        Raises:
            NotImplementedError: When the subclass does not implement this method.
        """
        raise NotImplementedError("Subclass must implement write_block method.")

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
