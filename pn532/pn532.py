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

from .utils.contants import (PN532_ERRORS,
                             _PREAMBLE,
                             _STARTCODE,
                             _POSTAMBLE,
                             _HOSTTOPN532,
                             _ACK,
                             _NACK,
                             _ISO14443A,
                             _PN532_CMD_INDATAEXCHANGE,
                             _PN532_CMD_GETFIRMWAREVERSION,
                             _PN532_CMD_SAMCONFIGURATION,
                             _PN532_CMD_INLISTPASSIVETARGET,
                             _NTAG_CMD_GET_VERSION,
                             _NTAG_CMD_READ,
                             _NTAG_CMD_FAST_READ,
                             _NTAG_CMD_COMPATIBILITY_WRITE,
                             _NTAG_CMD_WRITE,
                             _NTAG_CMD_READ_CNT,
                             _NTAG_ADDR_READ_CNT,
                             _NTAG_CMD_PWD_AUTH,
                             _NTAG_CMD_READ_SIG,
                             _NTAG_ADDR_READ_SIG)


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

    def _call_function(self, command, response_length=0, params=None, timeout=1):
        """
        Send specified command to the PN532
        """
        if params is None:
            params = []
        data = bytearray(2 + len(params))
        data[0] = _HOSTTOPN532
        data[1] = command & 0xFF
        for i, val in enumerate(params):
            data[2+i] = val
        try:
            self._write_frame(data)
        except OSError:
            self._wakeup()
            return None
        if not self._wait_for_ack(timeout):
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

    def _validate_data_length(self, data, length=255):
        """
        Validate the length of the data to be sent.

        :param data: The data to be validated.
        :param length: The maximum allowable length of the data.
        :raises ValueError: If the data length is not within the valid range.
        """
        if not data or not 1 < len(data) <= length:
            raise ValueError(f'Data must be an array of 1 to {length} bytes.')

    def _build_frame(self, packet_data=None, frame_type='normal'):
        """
        Handle the construction or parsing of a frame.

        :param data: The data for building or parsing.
        :param frame: The type of frame used to perform actions between the host and PN532.
        :return: Constructed or parsed frame.
        """
        frame = _PREAMBLE + _STARTCODE
        if frame_type == 'normal' and packet_data is not None:
            packet_length = len(packet_data)
            self._validate_data_length(packet_data, 255)
            packet_length_byte = packet_length.to_bytes(1, byteorder='big')
            frame += packet_length_byte

            packet_length_checksum = (~packet_length + 1 & 0xFF).to_bytes(1, byteorder='big')
            frame += packet_length_checksum
            
            frame += packet_data

            checksum = (sum(packet_data) + sum(_PREAMBLE + _STARTCODE + packet_length_byte + packet_length_checksum)) & 0xFF
            checksum_byte = (~checksum & 0xFF).to_bytes(1, byteorder='big')
            frame += checksum_byte
        elif frame_type == 'ack':
            frame += _ACK
        elif frame_type == 'nack':
            frame += _NACK
        elif frame_type == 'error':
            pass
        frame += _POSTAMBLE
        return frame
   
    def _parse_frame(self, packet_data):
        """
        Handle the construction or parsing of a frame.

        :param data: The data for building or parsing.
        :param frame: The type of frame used to perform actions between the host and PN532.
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
            parsed_data =  packet_data[offset+2:offset+2+frame_len]
            return parsed_data

    def _write_frame(self, data):
        """
        Write a frame to the PN532.
        """
        self._validate_data_length(data, 255)
        frame = self._build_frame(data, 'normal')
        self._write_data(bytes(frame))

    def _read_frame(self, length):
        """
        Read a response frame from the PN532.
        """
        response = self._read_data(length + 7)
        return self._parse_frame(response)

    def _wait_for_ack(self, timeout):
        """
        Wait for an ACK response within the given timeout.

        :param timeout: Time to wait for the ACK response.
        :return: True if ACK received, False otherwise.
        """
        ack_frame = self._build_frame(frame_type='ack')
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            ack = self._read_data(len(ack_frame))
            if ack == ack_frame:
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
        response = self._call_function(_PN532_CMD_INLISTPASSIVETARGET,
                                       params=[0x01, card_baud],
                                       response_length=19,
                                       timeout=timeout)
        if not response or response[0] != 0x01 or response[5] > 7:
            return None
        return response[6:6 + response[5]]

    def ntag2xx_write_block(self, block_number, data):
        """
        Write a block of data to the card.
        """
        self._validate_data_length(data, 4)
        response = self._call_function(_PN532_CMD_INDATAEXCHANGE,
                                      params=[0x01, _NTAG_CMD_WRITE, block_number & 0xFF, data],
                                      response_length=1)
        if response[0]:
            raise PN532Error(response[0])
        return response[0] == 0x00

    def ntag2xx_read_block(self, block_number):
        """
        Read a block of data from the card.
        """
        response = self._call_function(_PN532_CMD_INDATAEXCHANGE,
                                      params=[0x01, _NTAG_CMD_READ, block_number & 0xFF],
                                      response_length=17)
        if response[0]:
            raise PN532Error(response[0])
        return response[1:][0:4]
