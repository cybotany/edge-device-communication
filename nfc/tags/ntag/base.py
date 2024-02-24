from ..chip import BaseChip
from .constants import *

class NTAG(BaseChip):
    """
    This subclass provides concrete implementations for reading and writing to NTAGs.

    Attributes:
        memory (list[list[int]]): Memory representation of the NTAG.
    """
    block_size = 4
    read_cmd = NTAG_CMD_READ
    write_cmd = NTAG_CMD_WRITE

    def __init__(self, pn532, uid):
        """
        Initializes the NTAG with a PN532 instance and a unique identifier.

        Args:
            pn532 (PN532): The PN532 instance used for NFC communication.
            uid (str): The unique identifier for the NTAG.
        """
        super().__init__(pn532, uid)
        self.memory = []
        self._capability_container = self.read_block(3)
        if self._capability_container:
            # Byte 2 of the Capability Container has the tag type
            self._determine_tag_properties(self._capability_container[1])
            self._fill_memory()
        else:
            self._tag_type = 'Unknown'
            self._user_memory_range = (None, None)
            self._configuration_pages_range = (None, None)
            self._pages = None
            self.log("Failed to read capability container.", level="warning")

    def _determine_tag_properties(self, byte):
        """
        Fetches and caches a range of memory pages.
        """
        tag_properties_mapping = {
            0x12: ('NTAG213', (4, 39), (41, 44), 45),
            0x3E: ('NTAG215', (4, 129), (131, 134), 135),
            0x6D: ('NTAG216', (4, 225), (227, 230), 231),
        }
        properties = tag_properties_mapping.get(byte, ('Unknown', (None, None), (None, None), None))
        self._tag_type, self._user_memory_range, self._configuration_pages_range, self._pages = properties

    def _fill_memory(self):
        """
        Reads and caches the entire memory of the NTAG.

        Attempts to read each page of the NTAG's memory and cache it in the memory attribute.
        Logs and skips pages that fail to be read.
        """
        if not self.memory:
            self.memory = [[0x00 for _ in range(self.block_size)] for _ in range(self._pages)]
        for page in range(len(self.memory)):
            try:
                self.memory[page] = self.read_block(page)
            except Exception as e:
                self.log(f"Failed to read memory at page {page}: {e}", level="error")


    def _fetch_memory_range(self, start, end):
        """
        Fetches and caches a range of memory pages.
        """
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

    @property
    def tag_type(self):
        return self._tag_type

    @property
    def capability_container(self):
        """
        Returns the Capability Container of the NTAG.
        """
        return self._capability_container

    @property
    def user_memory(self):
        """
        Fetches and returns the user memory section of the NTAG.

        Returns:
            list[list[int]]: The user memory section if successfully fetched, None otherwise.
        """
        return self._fetch_memory_range(*self._user_memory_range)

    @property
    def configurations(self):
        """
        Fetches and returns the configuration pages of the NTAG.

        Returns:
            list[list[int]]: The configuration pages if successfully fetched, None otherwise.
        """
        return self._fetch_memory_range(*self._configuration_pages_range)

    def write_ndef_message(self, tnf, record_type, payload, id=''):
        # Simplified example for writing a URI record
        # This needs to be expanded to handle the NDEF message structure properly
        # Convert the payload to a format suitable for writing, e.g., a byte array
        data = bytearray(payload, 'utf-8')
        
        # Write data to user memory starting from the first user page
        # Assumes `data` fits within the user memory; you need to add checks and splitting for larger data
        current_page = self._user_memory_range[0]
        for i in range(0, len(data), self.block_size):
            block_data = data[i:i+self.block_size]
            if len(block_data) < self.block_size:
                block_data += bytearray(self.block_size - len(block_data))  # Pad with zeros
            self.write_block(current_page, list(block_data))
            current_page += 1
        return True

    def read_ndef_message(self):
        # Simplified example for reading from the user memory area
        # This needs proper parsing of the NDEF structure
        user_memory = self.user_memory
        message = bytearray()
        for page in user_memory:
            message += bytearray(page)
        # Here you would add parsing of the NDEF message from `message`
        # For simplicity, we're just converting it to a string
        return message.decode('utf-8')
