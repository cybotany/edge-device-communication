_NDEF_URIPREFIX_NONE = 0x00
_NDEF_URIPREFIX_HTTP_WWWDOT = 0x01
_NDEF_URIPREFIX_HTTPS_WWWDOT = 0x02
_NDEF_URIPREFIX_HTTP = 0x03
_NDEF_URIPREFIX_HTTPS = 0x04
_NDEF_URIPREFIX_TEL = 0x05
_NDEF_URIPREFIX_MAILTO = 0x06
_NDEF_URIPREFIX_FTP_ANONAT = 0x07
_NDEF_URIPREFIX_FTP_FTPDOT = 0x08
_NDEF_URIPREFIX_FTPS = 0x09
_NDEF_URIPREFIX_SFTP = 0x0A
_NDEF_URIPREFIX_SMB = 0x0B
_NDEF_URIPREFIX_NFS = 0x0C
_NDEF_URIPREFIX_FTP = 0x0D
_NDEF_URIPREFIX_DAV = 0x0E
_NDEF_URIPREFIX_NEWS = 0x0F
_NDEF_URIPREFIX_TELNET = 0x10
_NDEF_URIPREFIX_IMAP = 0x11
_NDEF_URIPREFIX_RTSP = 0x12
_NDEF_URIPREFIX_URN = 0x13
_NDEF_URIPREFIX_POP = 0x14
_NDEF_URIPREFIX_SIP = 0x15
_NDEF_URIPREFIX_SIPS = 0x16
_NDEF_URIPREFIX_TFTP = 0x17
_NDEF_URIPREFIX_BTSPP = 0x18
_NDEF_URIPREFIX_BTL2CAP = 0x19
_NDEF_URIPREFIX_BTGOEP = 0x1A
_NDEF_URIPREFIX_TCPOBEX = 0x1B
_NDEF_URIPREFIX_IRDAOBEX = 0x1C
_NDEF_URIPREFIX_FILE = 0x1D
_NDEF_URIPREFIX_URN_EPC_ID = 0x1E
_NDEF_URIPREFIX_URN_EPC_TAG = 0x1F
_NDEF_URIPREFIX_URN_EPC_PAT = 0x20
_NDEF_URIPREFIX_URN_EPC_RAW = 0x21
_NDEF_URIPREFIX_URN_EPC = 0x22
_NDEF_URIPREFIX_URN_NFC = 0x23

class NDEF:
    """
    Class for handling NDEF operations on an NTAG.

    This class should be subclassed to implement the read_ndef_message and write_ndef_message methods.

    :param ntag: An instance of the NTAG class that this NDEF class will operate on.
    """
    def __init__(self, ntag):
        """
        Initializes the NDEF class for handling NDEF operations on an NTAG.

        :param ntag: An instance of the NTAG class that this NDEF class will operate on.
        """
        self.ntag = ntag

    def _create_message_flags(self, payload, id, tnf):
        """
        Constructs the message flag byte for an NDEF record.

        :param payload: The payload of the NDEF record.
        :param id: The ID of the NDEF record.
        :param tnf: The Type Name Format of the NDEF record.
        :return: The constructed message flags byte.
        """
        MB, ME = 0x80, 0x40  # Message Begin, Message End
        CF, SR = 0x00, 0x10 if len(payload) < 256 else 0x00  # Chunk Flag, Short Record
        IL = 0x08 if id else 0x00  # ID Length
        return MB | ME | CF | SR | IL | tnf

    def _prepare_payload(self, record_type, payload):
        """
        Prepares the payload based on the record type.

        :param record_type: The type of the NDEF record.
        :param payload: The payload to be encoded.
        :return: The encoded payload.
        """
        uri_identifier_code = b'\x03' if self.ntag.debug else b'\x04'
        return uri_identifier_code + payload.encode() if record_type == 'U' else payload.encode()

    def _create_record_header(self, tnf, record_type, payload, id):
        """
        Creates the header for an NDEF record.

        :param tnf: The Type Name Format of the NDEF record.
        :param record_type: The type of the record.
        :param payload: The payload of the record.
        :param id: The ID of the record.
        :return: The constructed record header.
        """
        message_flags = self._create_message_flags(payload, id, tnf)
        prepared_payload = self._prepare_payload(record_type, payload)
        type_length, payload_length = len(record_type).to_bytes(1, 'big'), len(prepared_payload).to_bytes(1 if len(prepared_payload) < 256 else 4, 'big')
        id_length = len(id).to_bytes(1, 'big') if id else b''
        return bytes([message_flags]) + type_length + payload_length + id_length + record_type.encode() + (id.encode() if id else b''), prepared_payload

    def _construct_complete_record(self, tnf, record_type, payload, id):
        """
        Constructs the complete NDEF record including the TLV wrapper.

        :param tnf: The Type Name Format of the NDEF record.
        :param record_type: The type of the record.
        :param payload: The payload of the NDEF record.
        :param id: The ID of the record.
        :return: The complete NDEF record with TLV.
        """
        header, prepared_payload = self._create_record_header(tnf, record_type, payload, id)
        complete_record = header + prepared_payload
        tlv_length = len(complete_record).to_bytes(1 if len(complete_record) < 255 else 2, 'big')
        return b'\x03' + tlv_length + complete_record + b'\xFE'

    def write_ndef_message(self, tnf, record_type, payload, id='', start_block=4):
        """
        Writes an NDEF message to the specified NTAG, handling the message formatting,
        chunking, and writing process.

        :param tnf: Type Name Format for the NDEF record.
        :param record_type: The type of the record (e.g., 'T' for text, 'U' for URI).
        :param payload: The payload of the NDEF record.
        :param id: An optional record ID.
        :param start_block: The starting block number to write the message.
        """
        if start_block < 4 or start_block > self.ntag.max_block:
            self.ntag.log(f"Invalid start block {start_block} for NDEF message.", "error")
            raise ValueError("Invalid start block for NDEF message.")
        try:
            complete_record = self._construct_complete_record(tnf, record_type, payload, id)
            chunks = [complete_record[i:i+4] for i in range(0, len(complete_record), 4)]
            for i, chunk in enumerate(chunks, start=start_block):
                self.ntag.write_block(i, chunk + b'\x00' * (4 - len(chunk)))  # Pads chunk if necessary
            self.ntag.log("Successfully wrote NDEF message to the NFC tag.", "info")
        except IOError as e:
            self.ntag.log(f"I/O Error writing NDEF message to the tag: {e}", "error")
        except ValueError as e:
            self.ntag.log(f"Value Error in NDEF data: {e}", "error")

