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
        data_out: microcontroller.Pin,
        data_in: microcontroller.Pin,
        channels: int = 2,
        sample_rate: int = 48000,
        bits: int = 16,
        buffer_size: int = 1024,
    ):
        self._channels = channels
        self._sample_rate = sample_rate
        self._bits = bits
        self._buffer_size = buffer_size

        self._buffer_out = array.array("h", [0] * buffer_size)
        self._buffer_in = [array.array("h", [0] * buffer_size) for i in range(2)]  # double-buffered

        pioasm = f"""
.program i2s_codec
.side_set 2
    nop                    side 0b00 [3]
    nop                    side 0b01 [1]
    pull noblock           side 0b01 ; wrap_target
    set x {bits-2}         side 0b01
left_bit:
    out pins 1             side 0b00 [3]
    in pins 1              side 0b01 [2]
    jmp x-- left_bit       side 0b01
    out pins 1             side 0b10 [3] ; LSB
    in pins 1              side 0b11 [2]
    set x {bits-2}         side 0b11
right_bit:
    out pins 1             side 0b10 [3]
    in pins 1              side 0b11 [2]
    jmp x-- right_bit      side 0b11
    out pins 1             side 0b00 [3] ; Transfer LSB
    in pins 1              side 0b01
    push noblock           side 0b01
"""

        self._pio = rp2pio.StateMachine(
            adafruit_pioasm.assemble(pioasm),
            frequency=sample_rate * channels * bits * 8,
            wrap_target=2,
            first_out_pin=data_out,
            first_in_pin=data_in,
            first_sideset_pin=bit_clock,
            sideset_pin_count=2,
            pull_threshold=32,
            push_threshold=32,
            out_shift_right=False,
            in_shift_right=False,
        )

        # Begin double-buffered background read/write operations
        self._pio.background_read(
            loop=self._buffer_in[0],
            loop2=self._buffer_in[1],
        )

    def deinit(self) -> None:
        self._pio.stop()
        self._pio.deinit()
        del self._pio

    @property
    def channels(self) -> int:
        return self._channels

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    @property
    def bits(self) -> int:
        return self._bits

    def write(self, data: circuitpython_typing.ReadableBuffer) -> None:
        self._pio.background_write(once=self._buffer_out)

    def read(self) -> circuitpython_typing.ReadableBuffer:
        return self._pio.last_read
