# Waveshare PN532 NFC Hat control library.
# Author: Yehui from Waveshare
#
# The MIT License (MIT)
#
# Copyright (c) 2015-2018 Adafruit Industries
# Copyright (c) 2019 Waveshare
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
This module will let you communicate with a PN532 RFID/NFC chip
using UART (ttyS0) on the Raspberry Pi.
"""
import time
import serial
import RPi.GPIO as GPIO
from .pn532 import PN532, BusyError, PN532Error

DEV_SERIAL = '/dev/ttyS0'
BAUD_RATE = 115200

class PN532_UART(PN532):
    """
    Driver for the PN532 connected over UART.
    """
    def __init__(self, dev=DEV_SERIAL, baudrate=BAUD_RATE, irq=None, reset=None, debug=False):
        self._uart = serial.Serial(dev, baudrate)
        if not self._uart.is_open:
            raise RuntimeError(f'cannot open {dev}')
        # Initialize GPIOs if needed before calling super().__init__
        if irq is not None:
            self._setup_pin(irq, GPIO.IN)
        super().__init__(debug=debug, reset=reset)

    def _gpio_init(self, **kwargs):
        # Initialize GPIO pins specific to UART communication if needed.
        # This example assumes IRQ handling is the only GPIO operation not covered by the base class.
        pass

    def _reset(self):
        # Reset functionality might already be adequately handled by the base class.
        # If UART requires a specific reset sequence, implement it here.
        super()._reset()

    def _wakeup(self):
        # Specific wakeup commands for UART communication.
        self._uart.write(b'\x55\x55\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        self.SAM_configuration()

    def _wait_ready(self, timeout=0.001):
        # Wait for the UART device to be ready.
        timestamp = time.monotonic()
        while (time.monotonic() - timestamp) < timeout:
            if self._uart.in_waiting:
                return True
            else:
                time.sleep(0.05)
        return False

    def _read_data(self, count):
        # Read data from UART.
        frame = self._uart.read(min(self._uart.in_waiting, count))
        if not frame:
            raise BusyError("No data read from PN532")
        return frame

    def _write_data(self, framebytes):
        # Write data to UART.
        self._uart.read(self._uart.in_waiting)  # Clear buffer before writing
        self._uart.write(framebytes)