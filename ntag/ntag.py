class NTAG:
    def __init__(self, debug=False):
        """
        Initialize the NTAG instance.

        Args:
            debug (bool): Flag to enable debug output.
        """
        self.debug = debug
        # Initialize memory: 45 pages with 4 bytes per page
        self.memory = [[0x00] * 4 for _ in range(45)]
        self.password = None
        self.record_type = 'U'
        self.tnf = 0x01

        # Configure mirror and modulation settings
        self.mirror_conf = 0b11  # Enable both UID and NFC counter ASCII mirror
        self.mirror_byte = 0b01  # Start mirroring at the nth byte of the page
        self.strong_mod_en = 0b1 # Enable strong modulation mode
        self.mirror_page = 0x0C  # What page the mirror starts
        self.auth0 = 0x05        # Password protection enabled from this page
        self.rfu = 0x00              # RFU (Reserved for Future Use)

        # URL and identifier for the NDEF payload
        self.url = 'digidex.tech/links/?m='
        self.identifier = '00000000000000x00000'
        self.payload = self.url + self.identifier

        self._set_initial_configurations()

    def _set_initial_configurations(self):
        """
        Configure pre-programmed capabilities and NDEF magic numbers for NTAG213.
        """
        # Set NDEF magic numbers and default configuration pages
        self.memory[3] = [0xE1, 0x10, 0x12, 0x00]
        self.memory[4] = [0x01, 0x03, 0xA0, 0x0C]
        self.memory[5] = [0x34, 0x03, 0x00, 0xFE]

        # Configure mirror and modulation settings (Page 41)
        self.memory[41] = [
            (self.mirror_conf << 6) | (self.mirror_byte << 4) | (self.strong_mod_en << 2),
            self.rfu, self.mirror_page, self.auth0
        ]
        if self.debug:
            print("Initial configurations set.")

    def _create_message_flags(self, payload):
        """
        Create the NDEF message flags.
        """
        MB = 0x80  # Message Begin
        ME = 0x40  # Message End
        CF = 0x00  # Chunk Flag, not used for a single record
        SR = 0x10 if len(payload) < 256 else 0x00  # Short Record
        IL = 0x00  # ID Length
        return MB | ME | CF | SR | IL | self.tnf

    def _prepare_payload(self, payload):
        """
        Prepare the payload for the NDEF record.
        """
        if self.record_type == 'U':
            uri_identifier_code = b'\x04' 
            return uri_identifier_code + payload.encode()
        return payload.encode()

    def _create_record_header(self, message_flags, payload):
        """
        Create the header for the NDEF record.
        """
        type_length = len(self.record_type).to_bytes(1, byteorder='big')
        payload_length = len(payload).to_bytes(1 if len(payload) < 256 else 4, byteorder='big')
        id_length = b''
        record_type_bytes = self.record_type.encode()
        id_bytes = ''.encode()
        return bytes([message_flags]) + type_length + payload_length + id_length + record_type_bytes + id_bytes

    def _construct_complete_record(self, header, payload):
        """
        Construct the complete NDEF record with TLV wrapping.
        """
        complete_record = header + payload
        tlv_type = b'\x03'
        ndef_length = len(complete_record)
        tlv_length = bytes([ndef_length]) if ndef_length < 255 else b'\xFF' + ndef_length.to_bytes(2, byteorder='big')
        tlv = b'\x34' + tlv_type + tlv_length + complete_record + b'\xFE'  # Append terminator
        return tlv

    def create_ndef_record(self):
        """
        Create and return the NDEF record.
        """ 
        message_flags = self._create_message_flags(self.payload)
        prepared_payload = self._prepare_payload(self.payload)
        header = self._create_record_header(message_flags, prepared_payload)
        record = self._construct_complete_record(header, prepared_payload)
        return record
    
    def write_ndef(self, start_block=5):
        """
        Store the NDEF message in memory starting at the specified block.
        """
        record = self.create_ndef_record()
        
        # Calculate available memory and ensure record fits
        ndef_length = len(record)
        max_blocks = len(self.memory) - start_block
        if ndef_length > max_blocks * 4:
            raise ValueError("NDEF message is too long to fit in the available memory.")
        
        # Write the record into memory block by block
        try:
            for i in range(0, ndef_length, 4):
                block_data = record[i:i + 4]
                if len(block_data) < 4:
                    block_data += b'\x00' * (4 - len(block_data))
                self.memory[start_block + i // 4] = list(block_data)

            if self.debug:
                print("Successfully wrote all configurations and NDEF message to the in-memory NFC tag.")

        except Exception as e:
            print("Error writing NDEF message to the tag:", e)
