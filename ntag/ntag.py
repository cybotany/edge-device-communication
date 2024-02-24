from .base_ntag import BaseNTAG
from .ndef import NDEF

class NTAG(BaseNTAG):
    def __init__(self, pn532, debug=False):
        # Call the base class constructor
        super().__init__(pn532, debug=debug)

    def _initialize_memory(self):
        self.memory = [[0x00 for _ in range(4)] for _ in range(self.pages)]

