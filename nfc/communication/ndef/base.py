from .constants import *

class NDEF:
    """
    Utility class for handling NDEF (NFC Data Exchange Format) operations. 
    This class provides methods to format and parse NDEF messages, facilitating 
    the interaction with NFC tags through a PN532 controller.

    Attributes:
        pn532: An instance of a class derived from PN532 that this NDEF class will operate on.
    """

    def __init__(self, pn532):
        """
        Initializes the NDEF class with a reference to a PN532 object.
        
        Args:
            pn532: An instance of PN532 class for NFC communication.
        """
        self.pn532 = pn532

    @staticmethod
    def _create_message_flags(payload, id, tnf):
        """
        Constructs the message flag byte for an NDEF record.
        
        Args:
            payload: The payload of the NDEF record.
            id: The ID of the NDEF record.
            tnf: The Type Name Format of the NDEF record.
            
        Returns:
            The constructed message flags byte.
        """
        MB, ME = 0x80, 0x40  # Message Begin, Message End
        CF, SR = 0x00, 0x10 if len(payload) < 256 else 0x00  # Chunk Flag, Short Record
        IL = 0x08 if id else 0x00  # ID Length
        return MB | ME | CF | SR | IL | tnf

    @staticmethod
    def _prepare_payload(record_type, payload):
        """
        Prepares the payload based on the record type.
        
        Args:
            record_type: The type of the NDEF record.
            payload: The payload to be encoded.
            
        Returns:
            The encoded payload.
        """
        if record_type == 'U':  # URI record
            best_match_code = NDEF_URIPREFIX_NONE
            max_prefix_length = 0
            matched_prefix = ''
            
            # Find the best matching URI prefix
            for prefix, code in URI_PREFIX_MAP.items():
                if payload.startswith(prefix) and len(prefix) > max_prefix_length:
                    best_match_code = code
                    max_prefix_length = len(prefix)
                    matched_prefix = prefix
            
            payload = payload[len(matched_prefix):]  # Remove the matched prefix
            payload = bytes([best_match_code]) + payload.encode()  # Prepend the URI prefix code
        else:
            payload = payload.encode()  # Default to encoding as is
            
        return payload

    def _create_record_header(self, tnf, record_type, payload, id):
        """
        Creates the header for an NDEF record.
        
        Args:
            tnf: The Type Name Format of the NDEF record.
            record_type: The type of the record.
            payload: The payload of the record.
            id: The ID of the record.
            
        Returns:
            The constructed record header and the prepared payload.
        """
        message_flags = self._create_message_flags(payload, id, tnf)
        prepared_payload = self._prepare_payload(record_type, payload)
        type_length = len(record_type).to_bytes(1, 'big')
        payload_length = len(prepared_payload).to_bytes(1 if len(prepared_payload) < 256 else 4, 'big')
        id_length = len(id).to_bytes(1, 'big') if id else b''
        
        return (bytes([message_flags]) + type_length + payload_length + id_length +
                record_type.encode() + (id.encode() if id else b''), prepared_payload)

    def _construct_complete_record(self, tnf, record_type, payload, id):
        """
        Constructs the complete NDEF record, including the TLV wrapper.
        
        Args:
            tnf: The Type Name Format of the NDEF record.
            record_type: The type of the record.
            payload: The payload of the NDEF record.
            id: The ID of the record.
            
        Returns:
            The complete NDEF record with TLV wrapper.
        """
        header, prepared_payload = self._create_record_header(tnf, record_type, payload, id)
        complete_record = header + prepared_payload
        tlv_length = len(complete_record).to_bytes(1 if len(complete_record) < 255 else 2, 'big')
        
        return b'\x03' + tlv_length + complete_record + b'\xFE'  # NDEF message TLV block

    def write_ndef_message(self, tnf=TNF_EMPTY, record_type=None, payload=None, id='', start_block=4):
        """
        Writes an NDEF message to the NFC chip, leveraging the PN532 object for NFC communication.
        """
        if tnf == TNF_EMPTY:
            print("TNF_EMPTY passed. No NDEF message to write.")
            return

        complete_record = self._construct_complete_record(tnf, record_type, payload, id)
        
        # Adapt this method to use the PN532 object's capabilities for writing.
        # For example, using pn532.write_block() method for actual writing.
        # The specific implementation will depend on how your PN532 class is designed
        # to interact with NFC tags and how blocks/pages are written to NTAG/MIFARE.
        # This is a placeholder to indicate where to integrate writing logic.
        
        try:
            # Example of writing logic, assuming pn532 object has a method for writing NDEF.
            self.pn532.write_ndef_message(complete_record, start_block=start_block)
            print("Successfully wrote NDEF message to the NFC tag.")
        except Exception as e:
            print(f"Error writing NDEF message to the tag: {e}")
