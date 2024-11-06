# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: MIT
"""
`i2sinout`
================================================================================

Bidirectional I2S audio communication using PIO.


* Author(s): Cooper Dalrymple

Implementation Notes
--------------------

**Hardware:**

.. todo:: Add links to any specific hardware product page(s), or category page(s).
  Use unordered list & hyperlink rST inline format: "* `Link Text <url>`_"

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

.. todo:: Uncomment or remove the Bus Device and/or the Register library dependencies
  based on the library's use of either.

# * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
# * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

# imports

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/dcooperdalrymple/CircuitPython_I2SInOut.git"

import array

import adafruit_pioasm
import microcontroller
import rp2pio

try:
    import circuitpython_typing
except ImportError:
    pass


def _get_gpio_index(pin: microcontroller.Pin) -> int:
    for name in dir(microcontroller.pin):
        if getattr(microcontroller.pin, name) is pin:
            return int(name.replace("GPIO", ""))
    return None


class I2SInOut:
    def __init__(  # noqa: PLR0913
        self,
        bit_clock: microcontroller.Pin,
        word_select: microcontroller.Pin = None,
        data_out: microcontroller.Pin = None,
        data_in: microcontroller.Pin = None,
        channel_count: int = 2,
        sample_rate: int = 48000,
        bits_per_sample: int = 16,
        samples_signed: bool = True,
        buffer_size: int = 1024,
        peripheral: bool = False,
    ):
        if word_select and not rp2pio.pins_are_sequential([bit_clock, word_select]):
            raise ValueError("Word select pin must be sequential to bit clock pin")

        if peripheral and not data_in:
            raise ValueError("Data input pin must be specified in peripheral mode")

        if peripheral and not rp2pio.pins_are_sequential([data_in, bit_clock]):
            raise ValueError("Data input pin must come before bit clock pin sequentially")

        if channel_count < 1 or channel_count > 2:
            raise ValueError("Invalid channel count")

        if bits_per_sample % 8 != 0 or bits_per_sample < 8 or bits_per_sample > 32:
            raise ValueError("Invalid bits per sample")

        if buffer_size < 1:
            raise ValueError("Buffer size must be greater than 0")

        self._channel_count = channel_count
        self._sample_rate = sample_rate
        self._bits_per_sample = bits_per_sample
        self._buffer_size = buffer_size
        self._samples_signed = samples_signed

        self._writable = bool(data_out)
        self._readable = bool(data_in)

        left_channel_out = "out pins 1" if self._writable else "nop"
        right_channel_out = "out pins 1" if self._writable and channel_count > 1 else "nop"

        left_channel_in = "in pins 1" if self._readable else "nop"
        right_channel_in = "in pins 1" if self._readable and channel_count > 1 else "nop"

        if not peripheral:
            pioasm = f"""
.program i2s_codec
.side_set 2
    nop                         side 0b01
    set x {bits_per_sample-2}   side 0b01
left_bit:
    {left_channel_out}          side 0b00 [1]
    {left_channel_in}           side 0b01
    jmp x-- left_bit            side 0b01
    {left_channel_out}          side 0b10 [1]
    {left_channel_in}           side 0b11
    set x {bits_per_sample-2}   side 0b11
right_bit:
    {right_channel_out}         side 0b10 [1]
    {right_channel_in}          side 0b11
    jmp x-- right_bit           side 0b11
    {right_channel_out}         side 0b00 [1]
    {right_channel_in}          side 0b01
"""
        else:
            bit_clock_gpio = _get_gpio_index(bit_clock)
            word_select_gpio = _get_gpio_index(word_select) if word_select else bit_clock_gpio + 1
            pioasm = f"""
.program i2s_codec
.side_set 2
    wait 1 gpio {word_select_gpio}
    wait 1 gpio {bit_clock_gpio}
    wait 0 gpio {word_select_gpio}
    wait 0 gpio {bit_clock_gpio}
    set x {bits_per_sample-2}
    wait 1 gpio {bit_clock_gpio}
left_bit:
    wait 0 gpio {bit_clock_gpio}
    {left_channel_out}
    wait 1 gpio {bit_clock_gpio}
    {left_channel_in}
    jmp x-- left_bit
    wait 1 gpio {word_select_gpio}
    wait 0 gpio {bit_clock_gpio}
    {left_channel_out}
    wait 1 gpio {bit_clock_gpio}
    {left_channel_in}
    set x {bits_per_sample-2}
right_bit:
    wait 0 gpio {bit_clock_gpio}
    {right_channel_out}
    wait 1 gpio {bit_clock_gpio}
    {right_channel_in}
    jmp x-- right_bit
    wait 0 gpio {word_select_gpio}
    wait 0 gpio {bit_clock_gpio}
    {right_channel_out}
    wait 1 gpio {bit_clock_gpio}
    {right_channel_in}
"""

        self._pio = rp2pio.StateMachine(
            program=adafruit_pioasm.assemble(pioasm),
            wrap_target=1 if not peripheral else 4,
            frequency=sample_rate * bits_per_sample * 2 * (4 if not peripheral else 16),
            first_out_pin=data_out,
            out_pin_count=1,
            first_in_pin=data_in,
            in_pin_count=1 if not peripheral else 3,
            first_sideset_pin=bit_clock if not peripheral else None,
            sideset_pin_count=2 if not peripheral else 1,
            auto_pull=True,
            pull_threshold=bits_per_sample,
            out_shift_right=False,
            auto_push=True,
            push_threshold=bits_per_sample,
            in_shift_right=False,
        )

        # Begin double-buffered background read/write operations

        self._buffer_format = (
            "b" if bits_per_sample is 8 else ("h" if bits_per_sample is 16 else "l")
        )
        if not samples_signed:
            self._buffer_format = self._buffer_format.upper()

        if self._writable:
            self._buffer_out = [
                array.array(
                    self._buffer_format,
                    [0 if samples_signed else 2 ** (bits_per_sample - 1)] * buffer_size,
                )
                for i in range(2)
            ]  # double-buffered
            self._pio.background_write(
                loop=self._buffer_out[0],
                loop2=self._buffer_out[1],
            )
            self._write_index = 0
            self._last_write_index = -1

        if self._readable:
            self._buffer_in = [
                array.array(self._buffer_format, [0] * buffer_size) for i in range(2)
            ]  # double-buffered
            self._pio.background_read(
                loop=self._buffer_in[0],
                loop2=self._buffer_in[1],
            )

    def deinit(self) -> None:
        self._pio.stop()
        self._pio.deinit()
        del self._pio

    @property
    def channel_count(self) -> int:
        return self._channel_count

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def bits_per_sample(self) -> int:
        return self._bits_per_sample

    @property
    def samples_signed(self) -> bool:
        return self._samples_signed

    @property
    def buffer_size(self) -> int:
        return self._buffer_size

    @property
    def buffer_format(self) -> str:
        return self._buffer_format

    @property
    def writable(self) -> bool:
        return self._writable

    @property
    def write_index(self) -> int:
        if not self._writable:
            return None
        last_write = self._pio.last_write
        for i in range(2):
            if last_write is self._buffer_out[i]:
                self._write_index = i
                break
        return self._write_index

    @property
    def write_ready(self) -> bool:
        return self.write_index != self._last_write_index

    @property
    def write_buffer(self) -> array.array:
        if not self._writable:
            return None
        return self._buffer_out[self.write_index]

    @write_buffer.setter
    def write_buffer(self, value: circuitpython_typing.ReadableBuffer) -> None:
        if self._writable:
            idx = self.write_index
            for i in range(min(len(value), self._buffer_size)):
                self._buffer_out[idx][i] = value[i]
            self._last_write_index = idx

    def write(
        self, data: circuitpython_typing.ReadableBuffer, loop: bool = False, block: bool = True
    ) -> bool:
        if not self._writable or not data:
            return False
        if block:
            for i in range(2 if loop else 1):
                while not self.write_ready:
                    pass
                self.write_buffer = data
        elif loop:
            for i in range(self._buffer_size):
                self._buffer_out[0][i] = self._buffer_out[1][i] = data[i % len(data)]
        else:
            if not self.write_ready:
                return False
            self.write_buffer = data
        return True

    @property
    def readable(self) -> bool:
        return self._readable

    def read(self, block: bool = True) -> circuitpython_typing.ReadableBuffer:
        if not self._readable:
            return None
        if block:
            while not (data := self._pio.last_read):
                pass
            return data
        else:
            return self._pio.last_read
