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
using SPI on the Raspberry Pi.
"""
import time
import spidev
import RPi.GPIO as GPIO
from .pn532.base import PN532, BusyError, PN532Error

_SPI_STATREAD = 0x02
_SPI_DATAWRITE = 0x01
_SPI_DATAREAD = 0x03
_SPI_READY = 0x01


class SPIDevice:
    """
    Implements SPI device on spidev
    """
    def __init__(self, cs=None):
        self.spi = spidev.SpiDev(0, 0)
        GPIO.setmode(GPIO.BCM)
        self._cs = cs
        if cs:
            GPIO.setup(self._cs, GPIO.OUT)
            GPIO.output(self._cs, GPIO.HIGH)
        self.spi.max_speed_hz = 1000000
        self.spi.mode = 0b10    # CPOL=1 & CPHA=0

    def writebytes(self, buf):
        if self._cs:
            GPIO.output(self._cs, GPIO.LOW)
            time.sleep(0.001);
        ret = self.spi.writebytes(list(buf))
        if self._cs:
            time.sleep(0.001);
            GPIO.output(self._cs, GPIO.HIGH)
        return ret

    def readbytes(self, count):
        if self._cs:
            GPIO.output(self._cs, GPIO.LOW)
            time.sleep(0.001);
        ret = bytearray(self.spi.readbytes(count))
        if self._cs:
            time.sleep(0.001);
            GPIO.output(self._cs, GPIO.HIGH)
        return ret

    def xfer(self, buf):
        if self._cs:
            GPIO.output(self._cs, GPIO.LOW)
            time.sleep(0.001);
        buf = bytearray(self.spi.xfer(buf))
        if self._cs:
            time.sleep(0.001);
            GPIO.output(self._cs, GPIO.HIGH)
        return buf


def reverse_bit(num):
    """
    Turn an LSB byte to an MSB byte, and vice versa. Used for SPI as
    it is LSB for the PN532, but 99% of SPI implementations are MSB only!
    """
    result = 0
    for _ in range(8):
        result <<= 1
        result += (num & 1)
        num >>= 1
    return result


class PN532_SPI(PN532):
    """
    Driver for the PN532 connected over SPI.
    """
    def __init__(self, cs=None, irq=None, reset=None, debug=False):
        # Initialize SPI device
        self._spi = SPIDevice(cs)
        # Call the superclass constructor to handle common setup, including GPIO mode
        super().__init__(debug=debug, reset=reset)
        # Now handle SPI-specific GPIO setup
        self._gpio_init(cs=cs, irq=irq, reset=reset)

    def _gpio_init(self, reset=None, cs=None, irq=None):
        # Direct GPIO setup for SPI-specific pins
        self._cs = cs
        self._irq = irq
        if cs is not None:
            self._setup_pin(cs, GPIO.OUT, True)
        if irq is not None:
            self._setup_pin(irq, GPIO.IN)

    def _reset(self):
        # Implement the _reset method specific to SPI if needed
        super()._reset()

    def _wakeup(self):
        # SPI-specific wakeup commands
        time.sleep(1)
        self._spi.writebytes(bytearray([0x00]))
        time.sleep(1)

    def _wait_ready(self, timeout=1):
        # Poll the PN532 if the status byte is ready
        status = bytearray([reverse_bit(_SPI_STATREAD), 0])
        timestamp = time.monotonic()
        while (time.monotonic() - timestamp) < timeout:
            time.sleep(0.01)
            status = self._spi.xfer(status)
            if reverse_bit(status[1]) == _SPI_READY:
                return True
            time.sleep(0.005)
        return False

    def _read_data(self, count):
        # Read data from SPI
        frame = bytearray(count + 1)
        frame[0] = reverse_bit(_SPI_DATAREAD)
        frame = self._spi.xfer(frame)
        for i, val in enumerate(frame):
            frame[i] = reverse_bit(val)
        return frame[1:]

    def _write_data(self, framebytes):
        # Write data to SPI
        rev_frame = [reverse_bit(x) for x in bytes([_SPI_DATAWRITE]) + framebytes]
        self._spi.writebytes(bytes(rev_frame))
