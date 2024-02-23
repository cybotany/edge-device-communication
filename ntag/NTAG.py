from .AbstractNTAG import AbstractNTAG

MIFARE_CMD_AUTH_A = 0x60
MIFARE_CMD_AUTH_B = 0x61
MIFARE_CMD_READ = 0x30
MIFARE_CMD_WRITE = 0xA0
MIFARE_CMD_TRANSFER = 0xB0
MIFARE_CMD_DECREMENT = 0xC0
MIFARE_CMD_INCREMENT = 0xC1
MIFARE_CMD_STORE = 0xC2
MIFARE_ULTRALIGHT_CMD_WRITE = 0xA2

class NTAG(AbstractNTAG):
    """
    Concrete implementation of the AbstractNTAG class for specific NTAG NFC tags.

    This subclass provides concrete implementations for reading and writing to NTAG NFC tags,
    handling NDEF messages, and managing tag memory and configurations.

    Attributes:
        pn532 (PN532): Instance of PN532 class used for NFC communication.
        uid (str): Unique identifier of the NTAG.
        memory (list[list[int]]): Memory representation of the NTAG.
    """

    def __init__(self, pn532, uid):
        """
        Initializes the NTAG with a PN532 instance and a unique identifier.

        Args:
            pn532 (PN532): The PN532 instance used for NFC communication.
            uid (str): The unique identifier for the NTAG.
        """
        super().__init__(pn532, uid)
        self.uid = uid
        self.pn532 = pn532
        self.memory = [[0x00 for _ in range(4)] for _ in range(self.pages)] if self.pages else [] # Need to fix this

    @property
    def capability_container(self):
        """
        Fetches and caches the Capability Container of the NTAG.

        Returns:
            list[int]: The Capability Container if successfully fetched, None otherwise.
        """
        return self._fetch_section(3, 3)

    @property
    def user_memory(self):
        """
        Fetches and returns the user memory section of the NTAG.

        Returns:
            list[list[int]]: The user memory section if successfully fetched, None otherwise.
        """
        return self._fetch_memory_range(*self._get_user_memory_range())

    @property
    def configurations(self):
        """
        Fetches and returns the configuration pages of the NTAG.

        Returns:
            list[list[int]]: The configuration pages if successfully fetched, None otherwise.
        """
        return self._fetch_memory_range(*self._get_configuration_pages_range())

    def _fetch_memory_range(self, start, end):
        """
        Fetches and caches a range of memory pages.
        """
        # Check if start and end are not None and memory has been initialized
        if start is not None and end is not None and self.memory:
            return self.memory[start:end+1]
        return None

    def _fetch_section(self, start, end):
        """
        Fetch a specific memory section, caching the result.
        """
        section = getattr(self, f"_section_{start}_{end}", None)
        if section is None and self.memory:
            section = self.memory[start:end+1]
            setattr(self, f"_section_{start}_{end}", section)
        return section

    def _get_user_memory_range(self):
        tag_type = self.tag_type
        if tag_type == 'NTAG213':
            return 4, 39
        elif tag_type == 'NTAG215':
            return 4, 129
        elif tag_type == 'NTAG216':
            return 4, 225
        else:
            self.log("Unknown NTAG type. Cannot determine user memory range.", level="warning")
            return None, None

    def _get_configuration_pages_range(self):
        tag_type = self.tag_type
        if tag_type == 'NTAG213':
            return 41, 44
        elif tag_type == 'NTAG215':
            return 130, 134
        elif tag_type == 'NTAG216':
            return 226, 231
        else:
            self.log("Unknown NTAG type. Cannot determine configuration pages range.", level="warning")
            return None, None

    def fill_memory(self):
        """
        Reads and caches the entire memory of the NTAG.

        Attempts to read each page of the NTAG's memory and cache it in the memory attribute.
        Logs and skips pages that fail to be read.
        """
        if not self.memory:
            self.memory = [[0x00 for _ in range(4)] for _ in range(self.pages)] # need to fix self.pages
        for page in range(len(self.memory)):
            try:
                self.memory[page] = self.read_block(page)
            except Exception as e:
                self.log(f"Failed to read memory at page {page}: {e}", level="error")

    def read_block(self, block_number):
        """
        Read a block of data from the card.  Block number should be the block
        to read.  If the block is successfully read a bytearray of length 16 with
        data starting at the specified block will be returned.  If the block is
        not read then None will be returned.   
        """
        params = bytearray(3)
        params[0] = 0x01  # Max card numbers
        params[1] = MIFARE_CMD_READ
        params[2] = block_number & 0xFF

        response = self.pn532._call_function(params=params, response_length=17)
        # Return first 4 bytes since 16 bytes are always returned.
        return response[1:][:4]

    def write_block(self, block_number, data):
        """
        Write a block of data to the card.  Block number should be the block
        to write and data should be a byte array of length 4 with the data to
        write.  If the data is successfully written then True is returned,
        otherwise False is returned.
        """
        assert data is not None and len(data) == 4, 'Data must be an array of 4 bytes!'
        params = bytearray(3+len(data))
        params[0] = 0x01  # Max card numbers
        params[1] = MIFARE_ULTRALIGHT_CMD_WRITE
        params[2] = block_number & 0xFF
        params[3:] = data
        response = self.pn532._call_function(params=params, response_length=1)
        return response[0] == 0x00

    def fill_memory(self):
        # Fill memory only if not already initialized
        if not self.memory:
            self.memory = [[0x00 for _ in range(4)] for _ in range(self.pages)]
        for page in range(len(self.memory)):
            try:
                self.memory[page] = self.read_block(page)
            except Exception as e:
                self.log(f"Failed to read memory at page {page}: {e}", level="error")
