# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import array
import math

import board

import i2sinout

CHANNEL_COUNT = 2
SAMPLE_RATE = 22050
LENGTH = SAMPLE_RATE // 440

codec = i2sinout.I2SInOut(
    bit_clock=board.GP0,  # word select is GP1
    data_out=board.GP3,
    channel_count=CHANNEL_COUNT,
    sample_rate=SAMPLE_RATE,
    bits_per_sample=16,
    samples_signed=True,
    buffer_size=LENGTH * CHANNEL_COUNT,
)

# Generate one period of sine wave
sine_wave = array.array(codec.buffer_format, [0] * LENGTH * CHANNEL_COUNT)
for i in range(LENGTH):
    value = int(
        math.sin(math.pi * 2 * i / LENGTH) * ((2 ** (codec.bits_per_sample - 1)) - 1)
        + (2 ** (codec.bits_per_sample - 1) if not codec.samples_signed else 0)
    )
    for j in range(CHANNEL_COUNT):
        sine_wave[i * CHANNEL_COUNT + j] = value

# Write sine wave continuously
codec.write(sine_wave, loop=True)
