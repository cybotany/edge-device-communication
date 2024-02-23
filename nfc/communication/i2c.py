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
using I2C on the Raspberry Pi.
"""
import fcntl
import os
import time
import RPi.GPIO as GPIO
from .pn532 import PN532, BusyError, PN532Error

I2C_ADDRESS = 0x24
I2C_CHANNEL = 1
I2C_SLAVE = 1795


class I2CDevice:
    """
    Implements I2C device on ioctl
    """
    def __init__(self, channel, addr):
        self.addr = addr
        self.i2c = os.open('/dev/i2c-%d' % channel, os.O_RDWR)
        if self.i2c < 0:
            raise RuntimeError('i2c device does not exist')
        if fcntl.ioctl(self.i2c, I2C_SLAVE, addr) < 0:
            raise RuntimeError('i2c slave does not exist')

    def write(self, buf):
        """
        Wrapper method of os.write
        """
        return os.write(self.i2c, buf)

    def read(self, count):
        """
        Wrapper method of os.read
        """
        return os.read(self.i2c, count)


class PN532_I2C(PN532):
    """
    Driver for the PN532 connected over I2C.
    """
    def __init__(self, irq=None, reset=None, req=None, debug=False):
        """
        Create an instance of the PN532 class using I2C. Note that PN532
        uses clock stretching. Optional IRQ pin (not used),
        reset pin and debugging output.
        """
        self._i2c = I2CDevice(I2C_CHANNEL, I2C_ADDRESS)
        # Call the superclass constructor first to ensure GPIO is set up before calling _gpio_init
        super().__init__(debug=debug, reset=reset)
        # Now that GPIO.setmode has been called in the superclass, perform subclass-specific setup
        self._gpio_init(irq=irq, req=req, reset=reset)

    def _gpio_init(self, reset=None, irq=None, req=None):
        # Setup for IRQ and REQ pins specific to the I2C subclass
        if irq is not None:
            self._setup_pin(irq, GPIO.IN)
        if req is not None:
            self._setup_pin(req, GPIO.OUT, True)

    def _reset(self):
        # Implement the _reset method specific to I2C if needed
        if self.reset_pin is not None:
            GPIO.output(self.reset_pin, True)
            time.sleep(0.1)
            GPIO.output(self.reset_pin, False)
            time.sleep(0.5)
            GPIO.output(self.reset_pin, True)
            time.sleep(0.1)

    def _wakeup(self):
        # Implement the _wakeup method specific to I2C
        if self._req:
            GPIO.output(self._req, True)
            time.sleep(0.1)
            GPIO.output(self._req, False)
            time.sleep(0.1)
            GPIO.output(self._req, True)
            time.sleep(0.5)

    def _wait_ready(self, timeout=10):
        # Implement the _wait_ready method specific to I2C
        time.sleep(0.01)
        status = bytearray(1)
        timestamp = time.monotonic()
        while (time.monotonic() - timestamp) < timeout:
            try:
                status[0] = self._i2c.read(1)[0]
            except OSError:
                self._wakeup()
                continue
            if status == b'\x01':
                return True
            time.sleep(0.005)
        return False

    def _read_data(self, count):
        # Implement the _read_data method specific to I2C
        try:
            status = self._i2c.read(1)[0]
            if status != 0x01:
                raise BusyError
            frame = bytes(self._i2c.read(count+1))
        except OSError as err:
            if self.debug:
                print(err)
            return

        if self.debug:
            print("Reading: ", [hex(i) for i in frame[1:]])
        else:
            time.sleep(0.1)
        return frame[1:]

    def _write_data(self, framebytes):
        # Implement the _write_data method specific to I2C
        self._i2c.write(framebytes)
