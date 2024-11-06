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
import rp2pio

try:
    import circuitpython_typing
    import microcontroller
except ImportError:
    pass


class I2SInOut:
    def __init__(  # noqa: PLR0913
        self,
        bit_clock: microcontroller.Pin,
        data_out: microcontroller.Pin = None,
        data_in: microcontroller.Pin = None,
        channel_count: int = 2,
        sample_rate: int = 48000,
        bits_per_sample: int = 16,
        samples_signed: bool = True,
        buffer_size: int = 1024,
    ):
        
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

        self._pio = rp2pio.StateMachine(
            program=adafruit_pioasm.assemble(pioasm),
            wrap_target=1,
            frequency=sample_rate * bits_per_sample * 2 * 4,

            first_out_pin=data_out,
            out_pin_count=1,

            first_in_pin=data_in,
            in_pin_count=1,

            first_sideset_pin=bit_clock,
            sideset_pin_count=2,

            auto_pull=True,
            pull_threshold=bits_per_sample,
            out_shift_right=False,

            auto_push=True,
            push_threshold=bits_per_sample,
            in_shift_right=False,
        )

        # Begin double-buffered background read/write operations

        self._buffer_format = "b" if bits_per_sample is 8 else ("h" if bits_per_sample is 16 else "l")
        if not samples_signed:
            self._buffer_format = self._buffer_format.upper()
        
        if self._writable:
            self._buffer_silence = array.array(self._buffer_format, [0 if samples_signed else 2 ** (bits_per_sample - 1)] * buffer_size)
            self._pio.background_write(
                loop=self._buffer_silence,
            )
        
        if self._readable:
            self._buffer_in = [array.array(self._buffer_format, [0] * buffer_size) for i in range(2)]  # double-buffered
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

    def write(self, data: circuitpython_typing.ReadableBuffer, loop: bool = False) -> None:
        if self._writable:
            if loop:
                self._pio.background_write(
                    loop=data,
                )
            else:
                self._pio.background_write(
                    once=data,
                    loop=self._buffer_silence,
                )
    
    @property
    def readable(self) -> bool:
        return self._readable

    def read(self, block: bool = False) -> circuitpython_typing.ReadableBuffer:
        if not self._readable:
            return None
        if block:
            while not (data := self._pio.last_read):
                pass
            return data
        else:
            return self._pio.last_read
