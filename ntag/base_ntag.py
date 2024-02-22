from abc import ABC, abstractmethod
import logging

class BaseNTAG(ABC):
    """
    Base class for operations with NTAG NFC tags through a PN532 NFC/RFID controller.
    Designed to be subclassed for specific types of NTAGs, providing a common interface
    for NTAG detection, reading, and writing operations.

    Attributes:
        pn532 (PN532): The PN532 instance used for NFC communication.
        debug (bool): Enables debug logging when True.
        uid (bytes): The UID of the detected NTAG, populated after calling detect_tag().
        version (str): The version of the NTAG, derived from the Capability Container.
        memory_size_bytes (int): The total memory size of the NTAG in bytes.
        pages (int): The total number of memory pages in the NTAG.
        tag_type (str): The type of the NTAG ('NTAG213', 'NTAG215', 'NTAG216'), determined dynamically.

    Methods:
        detect_tag(): Attempts to detect an NTAG and read its UID. Returns the UID if successful.
        read_block(block_number): Reads a single memory block from the NTAG.
        write_block(block_number, data): Writes data to a single memory block in the NTAG.
        dump_memory(start_block=0, end_block=None): Prints the contents of memory blocks from start_block to end_block.
        read_ndef_message(): Abstract method placeholder for reading NDEF messages from the NTAG.
        write_ndef_message(ndef_message): Abstract method placeholder for writing NDEF messages to the NTAG.
        set_lock_bit(): Abstract method placeholder for making the NTAG read-only.

    The class utilizes property decorators for lazy loading of NTAG properties like version, memory_size_bytes,
    pages, and tag_type from the Capability Container, improving efficiency and encapsulating the logic within
    the property methods. These properties are computed only when accessed and cached for future use.

    Subclasses are expected to implement the _initialize_memory() method to set up the specific memory layout
    of the NTAG being targeted.
    """
    def __init__(self, pn532, debug=False):
        """
        Initializes the BaseNTAG with a PN532 instance and debug flag.
        
        Args:
            pn532 (PN532): The PN532 instance used for NFC communication.
            debug (bool): If true, enables detailed logging for debugging.
        """
        self.pn532 = pn532
        self.debug = debug
        self._cc = None  # Cache for the Capability Container, to be loaded on-demand

    @property
    def cc(self):
        """Lazily loads and returns the Capability Container from the NTAG."""
        if self._cc is None:
            try:
                self._cc = self.read_block(3)
            except Exception as e:
                self.log(f"Failed to read Capability Container: {e}", level="error")
        return self._cc

    @property
    def version(self):
        """Returns the NTAG version derived from the Capability Container."""
        if self.cc:
            major_version = (self.cc[1] >> 4) & 0x0F
            minor_version = self.cc[1] & 0x0F
            return f"{major_version}.{minor_version}"
        return None

    @property
    def memory_size_bytes(self):
        """Returns the NTAG memory size in bytes, calculated from the Capability Container."""
        if self.cc:
            return self.cc[2] * 8
        return None

    @property
    def pages(self):
        """Returns the number of memory pages in the NTAG."""
        if self.memory_size_bytes:
            return self.memory_size_bytes // 4
        return None

    @property
    def tag_type(self):
        """Determines the NTAG type based on its memory size."""
        if self.memory_size_bytes:
            if self.memory_size_bytes == 144:
                return 'NTAG213'
            elif self.memory_size_bytes == 504:
                return 'NTAG215'
            elif self.memory_size_bytes == 888:
                return 'NTAG216'
        self.log("Unable to determine NTAG type based on memory size.", level="warning")
        return None

    @abstractmethod
    def _initialize_memory(self):
        """
        Subclasses should implement this method to initialize the NTAG's memory layout.
        """
        pass

    def log(self, message, level="info", also_print=True):
        """
        Helper method to log messages and optionally print them to the console.
        """
        if level == "info":
            logging.info(message)
        elif level == "warning":
            logging.warning(message)
        elif level == "error":
            logging.error(message)

        if self.debug and also_print:
            print(message)

    def detect_tag(self):
        """
        Detects if an NTAG is present in the field and reads its UID.
        """
        uid = self.pn532.read_passive_target()
        if uid:
            self.uid = uid
            self.log(f"Tag detected with UID: {self.uid.hex()}")
            return True
        else:
            self.log("No tag detected.", level="warning")
            return False

    def read_block(self, block_number):
        """
        Read a single block from the NTAG.
        """
        if not (0 <= block_number < self.pages):
            self.log("Block number out of range", level="error", also_print=False)
            raise ValueError("Block number out of range")
        data = self.pn532.mifare_classic_read_block(block_number)
        if data is None:
            self.log(f"Failed to read block {block_number}", level="error", also_print=False)
            raise IOError(f"Failed to read block {block_number}")
        return data

    def write_block(self, block_number, data):
        """
        Write a single block to the NTAG.
        """
        if not (0 <= block_number < self.pages):
            self.log("Block number out of range", level="error", also_print=False)
            raise ValueError("Block number out of range")
        if not self.pn532.mifare_classic_write_block(block_number, data):
            self.log(f"Failed to write block {block_number}", level="error", also_print=False)
            raise IOError(f"Failed to write block {block_number}")

    def dump_memory(self, start_block=0, end_block=None):
        """
        Dumps the memory from start_block to end_block.
        """
        if end_block is None or end_block >= self.pages:
            end_block = self.pages - 1
        for block_number in range(start_block, end_block + 1):
            try:
                data = self.read_block(block_number)
                self.log(f"Block {block_number}: {data.hex()}")
            except IOError as e:
                self.log(f"Error reading block {block_number}: {e}", level="error")

    def read_ndef_message(self):
        """
        Placeholder for reading NDEF messages.
        Subclasses should implement reading logic based on tag memory structure
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def write_ndef_message(self, ndef_message):
        """
        Placeholder for writing NDEF messages.
        Subclasses should implement writing logic based on tag memory structure
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def set_lock_bit(self):
        """
        Placeholder for setting the lock bit.
        Subclasses should implement lock bit setting based on tag specifications
        """
        raise NotImplementedError("This method should be implemented by subclasses")
