# Waveshare PN532 NFC Hat control library.
# Author(s): Yehui from Waveshare
#            Tony DiCola
#
# The MIT License (MIT)
#
# Copyright (c) 2019 Waveshare
# Copyright (c) 2015-2018 Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
This module will let you communicate with a PN532 NFC Hat using I2C, SPI or UART.
The main difference is the interfaces implements.
"""
import RPi.GPIO as GPIO
import time

# Constants
_PREAMBLE                      = 0x00
_STARTCODE1                    = 0x00
_STARTCODE2                    = 0xFF
_POSTAMBLE                     = 0x00
_HOSTTOPN532                   = 0xD4
_PN532TOHOST                   = 0xD5
_WAKEUP                        = 0x55
_ISO14443A                     = 0x00
_VALIDATIONBIT                 = 0x80
_ACK                           = b'\x00\x00\xFF\x00\xFF\x00'
_FRAME_START                   = b'\x00\x00\xFF'

# PN532 Commands
_COMMAND_DIAGNOSE              = 0x00
_COMMAND_GETFIRMWAREVERSION    = 0x02
_COMMAND_GETGENERALSTATUS      = 0x04
_COMMAND_READREGISTER          = 0x06
_COMMAND_WRITEREGISTER         = 0x08
_COMMAND_READGPIO              = 0x0C
_COMMAND_WRITEGPIO             = 0x0E
_COMMAND_SETSERIALBAUDRATE     = 0x10
_COMMAND_SETPARAMETERS         = 0x12
_COMMAND_SAMCONFIGURATION      = 0x14
_COMMAND_POWERDOWN             = 0x16
_COMMAND_RFCONFIGURATION       = 0x32
_COMMAND_RFREGULATIONTEST      = 0x58
_COMMAND_INJUMPFORDEP          = 0x56
_COMMAND_INJUMPFORPSL          = 0x46
_COMMAND_INLISTPASSIVETARGET   = 0x4A
_COMMAND_INATR                 = 0x50
_COMMAND_INPSL                 = 0x4E
_COMMAND_INDATAEXCHANGE        = 0x40
_COMMAND_INCOMMUNICATETHRU     = 0x42
_COMMAND_INDESELECT            = 0x44
_COMMAND_INRELEASE             = 0x52
_COMMAND_INSELECT              = 0x54
_COMMAND_INAUTOPOLL            = 0x60
_COMMAND_TGINITASTARGET        = 0x8C
_COMMAND_TGSETGENERALBYTES     = 0x92
_COMMAND_TGGETDATA             = 0x86
_COMMAND_TGSETDATA             = 0x8E
_COMMAND_TGSETMETADATA         = 0x94
_COMMAND_TGGETINITIATORCOMMAND = 0x88
_COMMAND_TGRESPONSETOINITIATOR = 0x90
_COMMAND_TGGETTARGETSTATUS     = 0x8A

# NTAG Commands
NTAG_CMD_GET_VERSION                = 0x60
NTAG_CMD_READ                       = 0x30
NTAG_CMD_FAST_READ                  = 0x3A
NTAG_CMD_WRITE                      = 0xA2
NTAG_CMD_COMPATIBILITY_WRITE        = 0xA0
NTAG_CMD_READ_CNT                   = 0x39
NTAG_ADDR_READ_CNT                  = 0x02
NTAG_CMD_PWD_AUTH                   = 0x1B
NTAG_CMD_READ_SIG                   = 0x3C
NTAG_ADDR_READ_SIG                  = 0x00

# NDEF Record Types
NDEF_URIPREFIX_NONE                 = 0x00
NDEF_URIPREFIX_HTTP_WWWDOT          = 0x01
NDEF_URIPREFIX_HTTPS_WWWDOT         = 0x02
NDEF_URIPREFIX_HTTP                 = 0x03
NDEF_URIPREFIX_HTTPS                = 0x04
NDEF_URIPREFIX_TEL                  = 0x05
NDEF_URIPREFIX_MAILTO               = 0x06
NDEF_URIPREFIX_FTP_ANONAT           = 0x07
NDEF_URIPREFIX_FTP_FTPDOT           = 0x08
NDEF_URIPREFIX_FTPS                 = 0x09
NDEF_URIPREFIX_SFTP                 = 0x0A
NDEF_URIPREFIX_SMB                  = 0x0B
NDEF_URIPREFIX_NFS                  = 0x0C
NDEF_URIPREFIX_FTP                  = 0x0D
NDEF_URIPREFIX_DAV                  = 0x0E
NDEF_URIPREFIX_NEWS                 = 0x0F
NDEF_URIPREFIX_TELNET               = 0x10
NDEF_URIPREFIX_IMAP                 = 0x11
NDEF_URIPREFIX_RTSP                 = 0x12
NDEF_URIPREFIX_URN                  = 0x13
NDEF_URIPREFIX_POP                  = 0x14
NDEF_URIPREFIX_SIP                  = 0x15
NDEF_URIPREFIX_SIPS                 = 0x16
NDEF_URIPREFIX_TFTP                 = 0x17
NDEF_URIPREFIX_BTSPP                = 0x18
NDEF_URIPREFIX_BTL2CAP              = 0x19
NDEF_URIPREFIX_BTGOEP               = 0x1A
NDEF_URIPREFIX_TCPOBEX              = 0x1B
NDEF_URIPREFIX_IRDAOBEX             = 0x1C
NDEF_URIPREFIX_FILE                 = 0x1D
NDEF_URIPREFIX_URN_EPC_ID           = 0x1E
NDEF_URIPREFIX_URN_EPC_TAG          = 0x1F
NDEF_URIPREFIX_URN_EPC_PAT          = 0x20
NDEF_URIPREFIX_URN_EPC_RAW          = 0x21
NDEF_URIPREFIX_URN_EPC              = 0x22
NDEF_URIPREFIX_URN_NFC              = 0x23

PN532_ERRORS = {
    0x01: 'PN532 ERROR TIMEOUT',
    0x02: 'PN532 ERROR CRC',
    0x03: 'PN532 ERROR PARITY',
    0x04: 'PN532 ERROR COLLISION_BITCOUNT',
    0x05: 'PN532 ERROR MIFARE_FRAMING',
    0x06: 'PN532 ERROR COLLISION_BITCOLLISION',
    0x07: 'PN532 ERROR NOBUFS',
    0x09: 'PN532 ERROR RFNOBUFS',
    0x0a: 'PN532 ERROR ACTIVE_TOOSLOW',
    0x0b: 'PN532 ERROR RFPROTO',
    0x0d: 'PN532 ERROR TOOHOT',
    0x0e: 'PN532 ERROR INTERNAL_NOBUFS',
    0x10: 'PN532 ERROR INVAL',
    0x12: 'PN532 ERROR DEP_INVALID_COMMAND',
    0x13: 'PN532 ERROR DEP_BADDATA',
    0x14: 'PN532 ERROR MIFARE_AUTH',
    0x18: 'PN532 ERROR NOSECURE',
    0x19: 'PN532 ERROR I2CBUSY',
    0x23: 'PN532 ERROR UIDCHECKSUM',
    0x25: 'PN532 ERROR DEPSTATE',
    0x26: 'PN532 ERROR HCIINVAL',
    0x27: 'PN532 ERROR CONTEXT',
    0x29: 'PN532 ERROR RELEASED',
    0x2a: 'PN532 ERROR CARDSWAPPED',
    0x2b: 'PN532 ERROR NOCARD',
    0x2c: 'PN532 ERROR MISMATCH',
    0x2d: 'PN532 ERROR OVERCURRENT',
    0x2e: 'PN532 ERROR NONAD',
}

class PN532Error(Exception):
    """
    PN532 error code
    """
    def __init__(self, err):
        super().__init__(PN532_ERRORS.get(err, 'Unknown Error'))


class BusyError(Exception):
    """
    Exception for busy state errors.
    """
    pass


class PN532:
    """
    Driver for the PN532 NFC Hat. Extend for specific interfaces (I2C/SPI/UART).
    """

    def __init__(self, *, debug=False, reset=None):
        """
        Create an instance of the PN532 class
        """
        self.debug = debug
        if reset:
            self._reset(reset)
        self._initialize()

    def _gpio_init(self, **kwargs):
        """
        Hardware GPIO init
        """
        raise NotImplementedError

    def _get_firmware_version(self):
        """
        Retrieve the firmware version from the PN532.
        """
        response = self.call_function(_COMMAND_GETFIRMWAREVERSION, 4, timeout=0.5)
        if not response:
            raise RuntimeError('Failed to detect the PN532')
        return tuple(response)

    def _initialize(self):
        """
        Initialize the device and check its firmware version.
        """
        self._wakeup()
        try:
            self._get_firmware_version()
        except (BusyError, RuntimeError):
            self._get_firmware_version()

    def _reset(self, pin):
        """
        Perform a hardware reset toggle
        """
        raise NotImplementedError

    def _read_data(self, count):
        """
        Read raw data from device, not including status bytes:
        Subclasses MUST implement this!
        """
        raise NotImplementedError

    def _write_data(self, framebytes):
        """
        Write raw bytestring data to device, not including status bytes:
        Subclasses MUST implement this!
        """
        raise NotImplementedError

    def _wait_ready(self, timeout):
        """
        Check if busy up to max length of 'timeout' seconds
        Subclasses MUST implement this!
        """
        raise NotImplementedError

    def _wakeup(self):
        """
        Send special command to wake up
        """
        raise NotImplementedError

    def _write_frame(self, data):
        """
        Write a frame to the PN532.
        """
        self._validate_data_length(data, 255)
        frame = self._handle_frame(data, operation='build')
        self._write_data(bytes(frame))

    def _read_frame(self, length):
        """
        Read a response frame from the PN532.
        """
        response = self._read_data(length + 7)
        return self._handle_frame(response, operation='parse')

    def _validate_data_length(self, data, length=255):
        """
        Validate the length of the data to be sent.

        :param data: The data to be validated.
        :param length: The maximum allowable length of the data.
        :raises ValueError: If the data length is not within the valid range.
        """
        if not data or not 1 < len(data) <= length:
            raise ValueError(f'Data must be an array of 1 to {length} bytes.')

    def _handle_frame(self, data, operation='build'):
        """
        Handle the construction or parsing of a frame.

        :param data: The data for building or parsing.
        :param operation: 'build' for building a frame, 'parse' for parsing.
        :return: Constructed or parsed frame.
        """
        if operation == 'build':
            length = len(data)
            frame = bytearray(length + 7)
            return frame
        elif operation == 'parse':
            offset = 0
            while data[offset] == 0x00:
                offset += 1
                if offset >= len(data):
                    raise RuntimeError('Response frame preamble does not contain 0x00FF!')
            if data[offset] != 0xFF:
                raise RuntimeError('Response frame preamble does not contain 0x00FF!')
            offset += 1
            if offset >= len(data):
                raise RuntimeError('Response contains no data!')
            frame_len = data[offset]
            if (frame_len + data[offset+1]) & 0xFF != 0:
                raise RuntimeError('Response length checksum did not match length!')
            checksum = sum(data[offset+2:offset+2+frame_len+1]) & 0xFF
            if checksum != 0:
                raise RuntimeError('Response checksum did not match expected value.')
            parsed_data =  data[offset+2:offset+2+frame_len]
            return parsed_data

    def _prepare_command_data(self, command, params=None):
        """
        Prepare data for sending a command.

        :param command: The command byte.
        :param params: Optional parameters for the command.
        :return: Prepared data as bytearray.
        """
        if params is None:
            params = []
        data = bytearray(2 + len(params))
        data[0] = _HOSTTOPN532
        data[1] = command & 0xFF
        data[2:] = params
        return data

    def _wait_for_ack(self, timeout):
        """
        Wait for an ACK response within the given timeout.

        :param timeout: Time to wait for the ACK response.
        :return: True if ACK received, False otherwise.
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            ack = self._read_data(len(_ACK))
            if ack == _ACK:
                return True
        return False

    def _read_and_check_response(self, command, response_length, timeout):
        """
        Read and validate the response for a command
        """
        if not self._wait_ready(timeout):
            return None
        response = self._read_frame(response_length + 2)
        if response[0] != _PN532TOHOST or response[1] != (command + 1):
            raise RuntimeError('Unexpected command response')
        return response[2:]

    def call_function(self, command, response_length=0, params=None, timeout=1):
        """
        Send specified command to the PN532
        """
        data = self._prepare_command_data(command, params)
        self._write_frame(data)
        if not self._wait_for_ack(timeout):
            return None
        return self._read_and_check_response(command, response_length, timeout)

    def SAM_configuration(self):
        """
        Configure the PN532 for NTAG2xx reading.
        """
        self.call_function(_COMMAND_SAMCONFIGURATION, params=[0x01, 0x14, 0x01])

    def read_passive_target(self, card_baud=_ISO14443A, timeout=1):
        """
        Wait for an NTAG to be available and return its UID when found.
        """
        response = self.call_function(_COMMAND_INLISTPASSIVETARGET, params=[0x01, card_baud], response_length=19, timeout=timeout)
        if not response or response[0] != 0x01 or response[5] > 7:
            return None
        return response[6:6 + response[5]]

    def ntag2xx_get_version(self):
        """
        Send the GET_VERSION command to an NTAG chip and return its version information.

        :return: Tuple with version information or None if no response.
        """
        command = [NTAG_CMD_GET_VERSION]
        response = self.call_function(_COMMAND_INDATAEXCHANGE, params=command, response_length=8, timeout=1)
        if response is None or len(response) < 8:
            print("Failed to get version information or invalid response.")
            return None
        return tuple(response)

    def ntag2xx_read(self, start_page):
        """
        Read 16 bytes from the specified start page.
        """
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=[0x01, NTAG_CMD_READ, start_page & 0xFF],
                                      response_length=20)
        if response[0]:
            raise PN532Error(response[0])
        return response[1:]

    def ntag2xx_fast_read(self, start_page, end_page):
        """
        Read consecutive pages from start_page to end_page.
        """
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=[0x01, NTAG_CMD_FAST_READ, start_page & 0xFF, end_page & 0xFF],
                                      response_length=(end_page - start_page + 1) * 4 + 2)
        if response[0]:
            raise PN532Error(response[0])
        return response[1:]

    def ntag2xx_compatibility_write(self, page, data):
        """
        Write 4 bytes to a specific page using Compatibility Write.
        """
        self._validate_data_length(data, 4)
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=[0x01, NTAG_CMD_COMPATIBILITY_WRITE, page & 0xFF] + list(data),
                                      response_length=1)
        if response[0]:
            raise PN532Error(response[0])
        return response[0] == 0x00

    def ntag2xx_read_cnt(self):
        """
        Read the NTAG NFC counter value.
        """
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=[0x01, NTAG_CMD_READ_CNT, NTAG_ADDR_READ_CNT],
                                      response_length=4)
        if response[0]:
            raise PN532Error(response[0])
        return response[1:]

    def ntag2xx_pwd_auth(self, password):
        """
        Authenticate with the NTAG using a password.
        """
        self._validate_data_length(password, 4)
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=[0x01, NTAG_CMD_PWD_AUTH] + list(password),
                                      response_length=2)
        if response[0]:
            raise PN532Error(response[0])
        return response[1] == 0x00

    def ntag2xx_read_sig(self):
        """
        Read the NTAG signature.
        """
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=[0x01, NTAG_CMD_READ_SIG, NTAG_ADDR_READ_SIG],
                                      response_length=34)
        if response[0]:
            raise PN532Error(response[0])
        return response[1:]

    def ntag2xx_write_block(self, block_number, data):
        """
        Write a block of data to the card.
        """
        self._validate_data_length(data, 4)
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=[0x01, NTAG_CMD_WRITE, block_number & 0xFF, data],
                                      response_length=1)
        if response[0]:
            raise PN532Error(response[0])
        return response[0] == 0x00

    def ntag2xx_read_block(self, block_number):
        """
        Read a block of data from the card.
        """
        response = self.call_function(_COMMAND_INDATAEXCHANGE,
                                      params=[0x01, NTAG_CMD_READ, block_number & 0xFF],
                                      response_length=17)
        if response[0]:
            raise PN532Error(response[0])
        # Return first 4 bytes since 16 bytes are returned.
        return response[1:][0:4]

    def ntag2xx_create_record(self, tnf, record_type, payload):
        """
        Create an NDEF record.

        :param tnf: Type Name Format for the record
        :param record_type: Type of the record (e.g., URI, Text)
        :param payload: Data to store in the record
        :return: NDEF record as a byte array
        """
        ndef_record = bytearray()
        ndef_record.append(tnf)
        ndef_record.extend(record_type.encode('utf-8'))
        ndef_record.extend(payload.encode('utf-8'))
        return ndef_record

    def ntag2xx_write_record(self, ndef_record, start_block=4):
        """
        Write an NDEF record to an NTAG2XX NFC tag.

        :param ndef_record: NDEF record as a byte array
        :param start_block: Starting block number to write the record
        :return: True if write is successful, False otherwise
        """
        try:
            for i in range(0, len(ndef_record), 4):
                block_data = ndef_record[i:i + 4]
                if len(block_data) < 4:
                    block_data += b'\x00' * (4 - len(block_data))  # Padding
                self.ntag2xx_write_block(start_block + i // 4, block_data)
            return True
        except Exception as e:
            print("Error writing NDEF record to the tag:", e)
            return False
