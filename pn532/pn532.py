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

_HOSTTOPN532 = 0xD4
_PN532TOHOST = 0xD5
_PREAMBLE = 0x00
_STARTCODE1 = 0x00
_STARTCODE2 = 0xFF
_POSTAMBLE = 0x00
_WAKEUP = 0x55
_ISO14443A = 0x00
_VALIDATIONBIT = 0x80
_ACK = b'\x00\x00\xFF\x00\xFF\x00'
_NACK = b'\x00\xFF\x00\x00\xFF\x00'

# PN532 Miscellaneous Commands
_PN532_CMD_DIAGNOSE = 0x00
_PN532_CMD_GETFIRMWAREVERSION = 0x02
_PN532_CMD_GETGENERALSTATUS = 0x04
_PN532_CMD_READREGISTER = 0x06
_PN532_CMD_WRITEREGISTER = 0x08
_PN532_CMD_READGPIO = 0x0C
_PN532_CMD_WRITEGPIO = 0x0E
_PN532_CMD_SETSERIALBAUDRATE = 0x10
_PN532_CMD_SETPARAMETERS = 0x12
_PN532_CMD_SAMCONFIGURATION = 0x14
_PN532_CMD_POWERDOWN = 0x16

# PN532 Radio Frequency (RF) Communication Commands
_PN532_CMD_RFCONFIGURATION = 0x32
_PN532_CMD_RFREGULATIONTEST = 0x58

# PN532 initiator Commands
_PN532_CMD_INJUMPFORDEP = 0x56
_PN532_CMD_INJUMPFORPSL = 0x46
_PN532_CMD_INLISTPASSIVETARGET = 0x4A
_PN532_CMD_INATR = 0x50
_PN532_CMD_INPSL = 0x4E
_PN532_CMD_INDATAEXCHANGE = 0x40
_PN532_CMD_INCOMMUNICATETHRU = 0x42
_PN532_CMD_INDESELECT = 0x44
_PN532_CMD_INRELEASE = 0x52
_PN532_CMD_INSELECT = 0x54
_PN532_CMD_INAUTOPOLL = 0x60

# PN532 Target Commands
_PN532_CMD_TGINITASTARGET = 0x8C
_PN532_CMD_TGSETGENERALBYTES = 0x92
_PN532_CMD_TGGETDATA = 0x86
_PN532_CMD_TGSETDATA = 0x8E
_PN532_CMD_TGSETMETADATA = 0x94
_PN532_CMD_TGGETINITIATORCOMMAND = 0x88
_PN532_CMD_TGRESPONSETOINITIATOR = 0x90
_PN532_CMD_TGGETTARGETSTATUS = 0x8A

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
    0x12: 'PN532 ERROR DEP_INVALID_PN532_CMD',
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

    def _call_function(self, command=_PN532_CMD_INDATAEXCHANGE, response_length=0, params=None, timeout=1):
        """
        Send specified command to the PN532
        """
        if params is None:
            params = []
        packet_data = bytearray(2 + len(params))
        packet_data[0] = _HOSTTOPN532
        packet_data[1] = command & 0xFF
        for i, val in enumerate(params):
            packet_data[2+i] = val
        try:
            self._write_frame(packet_data)
        except OSError:
            self._wakeup()
            return None
        if not self._wait_for_ack():
            return None
        if not self._wait_ready(timeout):
            return None
        response = self._read_frame(response_length + 2)
        return response[2:]

    def _get_firmware_version(self):
        """
        Retrieve the firmware version from the PN532.
        """
        response = self._call_function(_PN532_CMD_GETFIRMWAREVERSION,
                                       response_length=4,
                                       timeout=0.5)
        if response is None:
            raise RuntimeError('Failed to detect the PN532')
        ic, ver, rev, support = tuple(response)
        if self.debug:
            print(f'Found PN532 with firmware version: {ver}.{rev}')
        return

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

    def _build_frame(self, packet_data):
        """
        Handle the construction of a frame.
        """
        packet_length = len(packet_data)
        frame = bytearray(packet_length + 7)
        frame[0] = _PREAMBLE
        frame[1] = _STARTCODE1
        frame[2] = _STARTCODE2
        checksum = sum(frame[0:3])
        frame[3] = packet_length & 0xFF
        frame[4] = (~packet_length + 1) & 0xFF
        frame[5:-2] = packet_data
        checksum += sum(packet_data)
        frame[-2] = ~checksum & 0xFF
        frame[-1] = _POSTAMBLE
        return frame
   
    def _parse_frame(self, packet_data):
        """
        Handle the parsing of a frame.

        :param data: The data for parsing.
        :return: Constructed or parsed frame.
        """
        offset = 0
        while packet_data[offset] == 0x00:
            offset += 1
            if offset >= len(packet_data):
                raise RuntimeError('Response frame preamble does not contain 0x00FF!')
        if packet_data[offset] != 0xFF:
            raise RuntimeError('Response frame preamble does not contain 0x00FF!')
        offset += 1
        if offset >= len(packet_data):
            raise RuntimeError('Response contains no data!')
        
        frame_len = packet_data[offset]
        if (frame_len + packet_data[offset+1]) & 0xFF != 0:
            raise RuntimeError('Response length checksum did not match length!')
        
        checksum = sum(packet_data[offset+2:offset+2+frame_len+1]) & 0xFF
        if checksum != 0:
            raise RuntimeError('Response checksum did not match expected value.')
        
        return packet_data[offset+2:offset+2+frame_len]

    def _write_frame(self, packet_data):
        """
        Write a frame to the PN532.
        """
        frame = self._build_frame(packet_data)
        self._write_data(bytes(frame))

    def _read_frame(self, length):
        """
        Read a response frame from the PN532.
        """
        response = self._read_data(length + 7)
        parsed_data = self._parse_frame(response)
        return parsed_data

    def _wait_for_ack(self):
        """
        Wait for an ACK response within the given timeout.
        """
        ack = self._read_data(len(_ACK))
        if ack == _ACK:
            return True
        return False

    def SAM_configuration(self):
        """
        Configure the PN532 to select the data flow path by configuring
        the internal serial data switch.

        :param mode: The method of using the SAM (Security Access Module).
        :param timeout: Defines the time-out only in Virtual card configuration.
        :param irq: Specifies if the PN532 takes care of the P70_IRQ pin or not.
        """
        self._call_function(_PN532_CMD_SAMCONFIGURATION, params=[0x01, 0x14, 0x01])

    def list_passive_target(self, card_baud=_ISO14443A, timeout=1):
        """
        Wait for an NTAG to be available and return its UID when found.
        The goal of this command is to detect as many targets (maximum MaxTg)
        as possible in passive mode. 
        """
        try:
            response = self._call_function(_PN532_CMD_INLISTPASSIVETARGET,
                                           params=[0x01, card_baud],
                                           response_length=19,
                                           timeout=timeout)
        except BusyError:
            return None
        # If no response is available return None to indicate no card is present.
        if response is None:
            return None
        # Check only 1 card with up to a 7 byte UID is present.
        if response[0] != 0x01:
            raise RuntimeError('More than one card detected!')
        if response[5] > 7:
            raise RuntimeError('Found card with unexpectedly long UID!')
        # Return UID of card.
        return response[6:6 + response[5]]
