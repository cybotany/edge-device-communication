from .constants import (_NTAG_CMD_READ, _NTAG_CMD_WRITE)


class NTAG:
    def __init__(self, pn532, debug=False):
        # Initialize memory: 45 pages, 4 bytes per page
        self.pn532 = pn532
        self.debug = debug
        self.memory = [[0x00 for _ in range(4)] for _ in range(45)]
        self._initialize_memory()

    def _initialize_memory(self):
        """
        Pre-programmed data as per NTAG213 specifications.
        Block 3: Capability Container
        Block 4: NDEF Magic Number
        Block 5: Pre-programmed data
        """
        self.memory[3] = [0xE1, 0x10, 0x12, 0x00]
        self.memory[4] = [0x01, 0x03, 0xA0, 0x0C]
        self.memory[5] = [0x34, 0x03, 0x00, 0xFE]

    def write_block(self, block_number, data):
        """
        Write a block of data to the card.
        """
        if not (0 <= block_number < 45):
            raise ValueError("Block number out of range")
        if not data or not 1 < len(data) <= 4:
            raise ValueError('Data must be an array of 1 to 4 bytes.')

        params = bytearray(3 + len(data))
        params[0] = 0x01
        params[1] = _NTAG_CMD_WRITE
        params[2] = block_number & 0xFF
        params[3:] = data
        response = self.pn532._call_function(params=params, response_length=1)
        if response[0]:
            print('Error writing block {}: {}'.format(block_number, response[0]))
        return response[0] == 0x00

    def read_block(self, block_number):
        """
        Read a block of data from the card.
        """
        if not (0 <= block_number < 45):
            raise ValueError("Block number out of range")

        params = [0x01, _NTAG_CMD_READ, block_number & 0xFF] 
        response = self.pn532._call_function(params=params,
                                             response_length=17)
        if response is None:
            print(f'Communication error while reading block {block_number}.')
            return None
        elif response[0] != 0x00:
            print(f'Error reading block {block_number}: {response[0]}')
            return None
        return response[1:][:4]

    def dump(self, start_block=0, end_block=44):
        """
        Reads specified range of pages (blocks) of the NTAG2xx NFC tag.
        """
        print(f"Reading NTAG213 NFC tag from block {start_block} to block {end_block}...")

        all_data = []
        for block_number in range(start_block, end_block + 1):
            block_data = self.read_block(block_number)
            if block_data is None:
                print(f"Error or no response while reading block {block_number}.")
                break

            formatted_block_data = ' '.join(['%02X' % x for x in block_data])
            all_data.append(formatted_block_data)

            if self.debug:
                print(f"Block {block_number}: {formatted_block_data}")

        return all_data

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
            uri_identifier_code = b'\x04' # b'\x03' if self.debug else b'\x04'
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