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
from abc import ABC, abstractmethod
import RPi.GPIO as GPIO
from .constants import *

class PN532Error(Exception):
    """
    PN532 error code
    """
    def __init__(self, err):
        Exception.__init__(self)
        self.err = err
        self.errmsg = PN532_ERROR_MAPPING[err]

class BusyError(Exception):
    """
    Exception for busy state errors.
    """
    pass


class PN532(ABC):
    """
    Driver for the PN532 NFC Hat. Extend for specific interfaces (I2C/SPI/UART).
    """
    def __init__(self, *, debug=False, reset=None):
        """
        Create an instance of the PN532 class
        """
        self.debug = debug
        GPIO.setmode(GPIO.BCM)
        if reset is not None:
            self._setup_pin(reset, GPIO.OUT, True)
            if self.debug:
                print('Resetting PN532.')
            self._reset()
        self._wakeup()

        try:
            self._get_firmware_version()  # first time often fails, try twice
        except (BusyError, RuntimeError):
            pass
        self._get_firmware_version()

    def _setup_pin(self, pin, direction, initial_state=False):
        GPIO.setup(pin, direction)
        if direction == GPIO.OUT:
            GPIO.output(pin, initial_state)

    @abstractmethod
    def _gpio_init(self, **kwargs):
        """
        Hardware GPIO init. Subclasses MUST implement this!
        """
        pass

    @abstractmethod
    def _reset(self):
        """
        Perform a hardware reset toggle. Subclasses MUST implement this!
        """
        pass

    @abstractmethod
    def _wakeup(self):
        """
        Send special command to wake up. Subclasses MUST implement this!
        """
        pass

    @abstractmethod
    def _read_data(self, count):
        """
        Read raw data from device, not including status bytes.
        Subclasses MUST implement this!
        """
        pass

    @abstractmethod
    def _write_data(self, framebytes):
        """
        Write raw bytestring data to device, not including status bytes.
        Subclasses MUST implement this!
        """
        pass

    @abstractmethod
    def _wait_ready(self, timeout):
        """
        Check if busy up to max length of 'timeout' seconds.
        Subclasses MUST implement this!
        """
        pass

    def _call_function(self, command=PN532_CMD_INDATAEXCHANGE, response_length=0, params=None, timeout=1):
        """
        Send specified command to the PN532
        """
        if params is None:
            params = []
        packet_data = bytearray(2 + len(params))
        packet_data[0] = HOSTTOPN532
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
        response = self._call_function(PN532_CMD_GETFIRMWAREVERSION,
                                       response_length=4,
                                       timeout=0.5)
        if response is None:
            raise RuntimeError('Failed to detect the PN532')
        ic, ver, rev, support = tuple(response)
        if self.debug:
            print(f'Found PN532 with firmware version: {ver}.{rev}')
        return

    def _build_frame(self, packet_data):
        """
        Handle the construction of a frame.
        """
        packet_length = len(packet_data)
        frame = bytearray(packet_length + 7)
        frame[0] = PREAMBLE
        frame[1] = STARTCODE1
        frame[2] = STARTCODE2
        checksum = sum(frame[0:3])
        frame[3] = packet_length & 0xFF
        frame[4] = (~packet_length + 1) & 0xFF
        frame[5:-2] = packet_data
        checksum += sum(packet_data)
        frame[-2] = ~checksum & 0xFF
        frame[-1] = POSTAMBLE
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
        ack = self._read_data(len(ACK))
        if ack == ACK:
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
        self._call_function(PN532_CMD_SAMCONFIGURATION, params=[0x01, 0x14, 0x01])

    def list_passive_target(self, card_baud=ISO14443A, timeout=1):
        """
        Wait for an NTAG to be available and return its UID when found.
        The goal of this command is to detect as many targets (maximum MaxTg)
        as possible in passive mode. 
        """
        try:
            response = self._call_function(PN532_CMD_INLISTPASSIVETARGET,
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

    def read_gpio(self, pin=None):
        """
        Read the state of the PN532's GPIO pins.

        :params pin: <str> specified the pin to read
        :return:

        If 'pin' is None, returns 3 bytes containing the pin state where:
            P3[0] = P30,   P7[0] = 0,   I[0] = I0,
            P3[1] = P31,   P7[1] = P71, I[1] = I1,
            P3[2] = P32,   P7[2] = P72, I[2] = 0,
            P3[3] = P33,   P7[3] = 0,   I[3] = 0,
            P3[4] = P34,   P7[4] = 0,   I[4] = 0,
            P3[5] = P35,   P7[5] = 0,   I[5] = 0,
            P3[6] = 0,     P7[6] = 0,   I[6] = 0,
            P3[7] = 0,     P7[7] = 0,   I[7] = 0,
        If 'pin' is not None, returns the specified pin state.
        """
        response = self._call_function(PN532_CMD_READGPIO, response_length=3)
        if not pin:
            return tuple(response[:3])
        pins = {'p3': response[0], 'p7': response[1], 'i': response[2]}
        if pin[:-1].lower() not in pins.keys():
            return False
        return True if pins[pin[:-1].lower()] >> int(pin[-1]) & 1 else False

    def write_gpio(self, pin=None, state=None, p3=None, p7=None):
        """
        Write the state to the PN532's GPIO pins.

        :params pin: <str> specified the pin to write
        :params state: <bool> pin level
        :params p3: byte to set multiple pins level
        :params p7: byte to set multiple pins level

        If p3 or p7 is not None, set the pins with p3 or p7, there is
        no need to read pin states before write with the param p3 or p7
        bits:
            P3[0] = P30,   P7[0] = 0,
            P3[1] = P31,   P7[1] = P71,
            P3[2] = P32,   P7[2] = P72,
            P3[3] = P33,   P7[3] = nu,
            P3[4] = P34,   P7[4] = nu,
            P3[5] = P35,   P7[5] = nu,
            P3[6] = nu,    P7[6] = nu,
            P3[7] = Val,   P7[7] = Val,
        For each port that is validated (bit Val = 1), all the bits are applied
        simultaneously. It is not possible for example to modify the state of
        the port P32 without applying a value to the ports P30, P31, P33, P34
        and P35.

        If p3 and p7 are None, set one pin with the params 'pin' and 'state'
        """
        params = bytearray(2)
        if (p3 is not None) or (p7 is not None):
            # 0x80, the validation bit.
            params[0] = 0x80 | p3 & 0xFF if p3 else 0x00
            params[1] = 0x80 | p7 & 0xFF if p7 else 0x00
            self._call_function(PN532_CMD_WRITEGPIO, params=params)
        else:
            if pin[:-1].lower() not in ('p3', 'p7'):
                return
            p3, p7, _ = self.read_gpio()
            if pin[:-1].lower() == 'p3':
                if state:
                    # 0x80, the validation bit.
                    params[0] = 0x80 | p3 | (1 << int(pin[-1])) & 0xFF
                else:
                    params[0] = 0x80 | p3 & ~(1 << int(pin[-1])) & 0xFF
                params[1] = 0x00    # leave p7 unchanged
            if pin[:-1].lower() == 'p7':
                if state:
                    # 0x80, the validation bit.
                    params[1] = 0x80 | p7 | (1 << int(pin[-1])) & 0xFF
                else:
                    params[1] = 0x80 | p7 & ~(1 << int(pin[-1])) & 0xFF
                params[0] = 0x00    # leave p3 unchanged
            self._call_function(PN532_CMD_WRITEGPIO, params=params)

    def tg_init_as_target(self, mode, mifare_params=None, felica_params=None, nfcid3t=None, gt=None, tk=None, timeout=60):
        """
        The host controller uses this command to configure the PN532 as
        target.

        :params mode: a byte indicating which mode the PN532 should respect.
        :params mifare_params: information needed to be able to be
        activated at 106 kbps in passive mode.
        :params felica_params: information to be able to respond to a polling
        request at 212/424 kbps in passive mode.
        :params nfcid3t: used in the ATR_RES in case of ATR_REQ received from
        the initiator
        :params gt: an array containing the general bytes to be used in the
        ATR_RES. This information is optional and the length is not fixed
        (max. 47 bytes),
        :params tk: an array containing the historical bytes to be used in the
        ATS when PN532 is in ISO/IEC14443-4 PICC emulation mode. This
        information is optional.
    
        :returns mode: a byte indicating in which mode the PN532 has been
        activated.
        :returns initiator_command: an array containing the first valid frame
        received by the PN532 once the PN532 has been initialized.
        """
        if not mifare_params:
            mifare_params = [0] * 6
        if not felica_params:
            felica_params = [0] * 18
        if not nfcid3t:
            nfcid3t = [0] * 10
        params = []
        params.append(mode)
        params += mifare_params
        params += felica_params
        params += nfcid3t
        if gt:
            params.append(len(gt))
            params += gt
        else:
            params.append(0x00)
        if tk:
            params.append(len(tk))
            params += tk
        else:
            params.append(0x00)
        # Try to read 64 bytes although the response length is not fixed
        response = self._call_function(PN532_CMD_TGINITASTARGET, 64, params=params, timeout=timeout)
        if response:
            mode_activated = response[0]
            initiator_command = response[1:]
            return (mode_activated, initiator_command)
