from ..nfc.chip.AbstractChip import NFC

class NTAG(NFC):
    def __init__(self, pn532, debug=False):
        # Call the base class constructor
        # Note: BaseNTAG now dynamically initializes memory based on tag type,
        # so we don't need to set it here.
        super().__init__(pn532, debug=debug)
        # Override tag_type and pages if necessary, or ensure it's set correctly in BaseNTAG
        self.tag_type = 'NTAG213'  # This might be redundant if BaseNTAG already determines it
        self.pages = 45  # NTAG213 has 45 pages. This might be redundant.

    def _initialize_memory(self):
        """
        Pre-programmed data as per NTAG213 specifications.
        Block 3: Capability Container
        Block 4: NDEF Magic Number
        Block 5: Pre-programmed data
        """
        super()._initialize_memory()
        self.memory[3] = [0xE1, 0x10, 0x12, 0x00]
        self.memory[4] = [0x01, 0x03, 0xA0, 0x0C]
        self.memory[5] = [0x34, 0x03, 0x00, 0xFE]

    def read_config_page(self, page):
        if not (_CONFIG_PAGE_START <= page <= _CONFIG_PAGE_END):
            raise ValueError("Page number out of configuration range")
        return self.read_block(page)

    def write_config_page(self, page, data):
        if not (_CONFIG_PAGE_START <= page <= _CONFIG_PAGE_END):
            raise ValueError("Page number out of configuration range")
        self.write_block(page, data)

    def get_mirror_configuration(self):
        config_page = self.read_config_page(41)  # Page 41 (0x29) for NTAG213
        mirror_conf = (config_page[0] >> _MIRROR_CONF_BIT_POS) & 0b11
        mirror_byte = (config_page[0] >> _MIRROR_BYTE_BIT_POS) & 0b11
        mirror_page = config_page[2]  # The byte itself is the MIRROR_PAGE value
        return mirror_conf, mirror_byte, mirror_page

    def set_mirror_configuration(self, mirror_conf, mirror_byte, mirror_page):
        config_page = self.read_config_page(41)  # Page 41 (0x29) for NTAG213
        # Set MIRROR_CONF and MIRROR_BYTE
        config_page[0] &= ~((0b11 << _MIRROR_CONF_BIT_POS) | (0b11 << _MIRROR_BYTE_BIT_POS))
        config_page[0] |= ((mirror_conf << _MIRROR_CONF_BIT_POS) | (mirror_byte << _MIRROR_BYTE_BIT_POS))
        # Set MIRROR_PAGE
        config_page[2] = mirror_page
        self.write_config_page(41, config_page)

    def update_memory_with_mirror(self):
        mirror_conf, mirror_byte, mirror_page = self.get_mirror_configuration()
        if mirror_conf in [0b01, 0b10, 0b11]:  # Check if UID/NFC counter mirroring is enabled
            # Convert UID and NFC counter to ASCII hex representation
            uid_ascii = ''.join(f'{byte:02X}' for byte in self.uid)
            nfc_counter_ascii = f'{self.nfc_counter:06X}'

            # Construct the mirrored string
            mirrored_string = uid_ascii + 'x' + nfc_counter_ascii if mirror_conf == 0b11 else \
                              uid_ascii if mirror_conf == 0b01 else \
                              nfc_counter_ascii

            # Write the mirrored string to memory starting from MIRROR_PAGE
            byte_index = mirror_byte
            for char in mirrored_string:
                page = mirror_page + byte_index // 4
                byte_pos = byte_index % 4
                self.memory[page][byte_pos] = ord(char)  # Convert char to ASCII value
                byte_index += 1

    def _create_message_flags(self, payload, id, tnf):
        # Assuming 'only' position if there's a single record
        MB = 0x80  # Message Begin
        ME = 0x40  # Message End
        CF = 0x00  # Chunk Flag, not used for a single record
        SR = 0x10 if len(payload) < 256 else 0x00  # Short Record
        IL = 0x08 if id else 0x00  # ID Length
        return MB | ME | CF | SR | IL | tnf


    def _prepare_payload(self, record_type, payload):
        if record_type == 'U':
            # Choose the URI identifier code based on the debug flag
            uri_identifier_code = b'\x03' if self.debug else b'\x04'
            return uri_identifier_code + payload.encode()
        return payload.encode()

    def _create_record_header(self, message_flags, record_type, payload, id):
        type_length = len(record_type).to_bytes(1, byteorder='big')
        payload_length = len(payload).to_bytes(1 if len(payload) < 256 else 4, byteorder='big')
        id_length = len(id).to_bytes(1, byteorder='big') if id else b''
        record_type_bytes = record_type.encode()
        id_bytes = id.encode()
        return bytes([message_flags]) + type_length + payload_length + id_length + record_type_bytes + id_bytes

    def _construct_complete_record(self, header, payload):
        complete_record = header + payload
        tlv_type = b'\x03'
        ndef_length = len(complete_record)
        tlv_length = bytes([ndef_length]) if ndef_length < 255 else b'\xFF' + ndef_length.to_bytes(2, byteorder='big')
        tlv = b'\x34' + tlv_type + tlv_length + complete_record + b'\xFE'  # Append terminator
        return tlv


    def create_ndef_record(self, tnf=0x01, record_type='T', payload='', id=''):
        """
        Method to create the NDEF record with debug statements.
        """
        message_flags = self._create_message_flags(payload, id, tnf)
        prepared_payload = self._prepare_payload(record_type, payload)
        header = self._create_record_header(message_flags, record_type, prepared_payload, id)
        return self._construct_complete_record(header, prepared_payload)
    
    def write_ndef_message(self, ndef_message, start_block=5):
        """
        Write an NDEF message to an NTAG2XX NFC tag.

        :param ndef_message: NDEF message as a byte array (can contain multiple records)
        :param start_block: Starting block number to write the message
        :return: True if write is successful, False otherwise
        """
        try:
            for i in range(0, len(ndef_message), 4):
                block_data = ndef_message[i:i + 4]
                if len(block_data) < 4:
                    block_data += b'\x00' * (4 - len(block_data))

                if self.debug:
                    print(f"Writing data to block {start_block + i // 4}: {block_data}")

                self.write_block(start_block + i // 4, block_data)

            if self.debug:
                print("Successfully wrote NDEF message to the NFC tag.")

            return True
        except Exception as e:
            print("Error writing NDEF message to the tag:", e)
            return False


__all__ = [
    'i2c',
    'spi',
    'uart',
    'PN532_I2C',
    'PN532_SPI',
    'PN532_UART'
]
from .communication.i2c import PN532_I2C
from .communication.spi import PN532_SPI
from .communication.uart import PN532_UART
