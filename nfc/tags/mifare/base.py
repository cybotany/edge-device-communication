from ..chip import BaseChip
from .constants import *

class MIFARE(BaseChip):
    """
    This subclass provides concrete implementations for reading and writing to MIFARE tags.

    Attributes:
        memory (list[list[int]]): Memory representation of the MIFARE tag.
    """
    block_size = 16
    read_cmd = MIFARE_CMD_READ
    write_cmd = MIFARE_ULTRALIGHT_CMD_WRITE

    def __init__(self, pn532, uid):
        """
        Initializes the MIFARE with a PN532 instance, unique identifier and memory representation.
        """
        super().__init__(pn532, uid)
        self.memory = []
        self._capability_container = self.read_block(3)
        if self._capability_container:
            # Byte 2 of the Capability Container has the tag type
            self._determine_tag_properties(self._capability_container[1])
        else:
            self._tag_type = 'Unknown'
            self._user_memory_range = (None, None)
            self._configuration_pages_range = (None, None)
            self._pages = None
            self.log("Failed to read capability container.", level="warning")

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

    @property
    def capability_container(self):
        """
        Fetches and caches the Capability Container of the MIFARE.

        Returns:
            list[int]: The Capability Container if successfully fetched, None otherwise.
        """
        return self._fetch_section(3, 3)

    @property
    def user_memory(self):
        """
        Fetches and returns the user memory section of the MIFARE.

        Returns:
            list[list[int]]: The user memory section if successfully fetched, None otherwise.
        """
        return self._fetch_memory_range(*self._user_memory_range)

    @property
    def configurations(self):
        """
        Fetches and returns the configuration pages of the MIFARE.

        Returns:
            list[list[int]]: The configuration pages if successfully fetched, None otherwise.
        """
        return self._fetch_memory_range(*self._configuration_pages_range)

    def fill_memory(self):
        """
        Reads and caches the entire memory of the MIFARE.

        Attempts to read each page of the MIFARE's memory and cache it in the memory attribute.
        Logs and skips pages that fail to be read.
        """
        if not self.memory:
            self.memory = [[0x00 for _ in range(self.block_size)] for _ in range(self._pages)]
        for page in range(len(self.memory)):
            try:
                self.memory[page] = self.read_block(page)
            except Exception as e:
                self.log(f"Failed to read memory at page {page}: {e}", level="error")
