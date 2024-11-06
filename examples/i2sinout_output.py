# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import array
import board
import i2sinout
import math

codec = i2sinout.I2SInOut(
    bit_clock=board.GP0, # word select is GP1
    data_out=board.GP3,
    channel_count=2,
    sample_rate=22050,
    bits_per_sample=16,
    samples_signed=True,
    buffer_size=1024,
)

# Generate one period of sine wave
length = codec.sample_rate // 440
sine_wave = array.array(codec.buffer_format, [0] * codec.buffer_size)
for i in range(codec.buffer_size // codec.channel_count):
    value = int(math.sin(math.pi * 2 * i / length) * ((2 ** (codec.bits_per_sample - 1)) - 1) + (2 ** (codec.bits_per_sample - 1) if not codec.samples_signed else 0))
    for j in range(codec.channel_count):
        sine_wave[i * codec.channel_count + j] = value

# Write sine wave continuously
codec.write(sine_wave, loop=True)
# NOTE: There will be distortion in the sine_wave as it loops across the bounds of the buffer
