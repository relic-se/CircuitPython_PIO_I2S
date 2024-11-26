# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import adafruit_wave
import board

import pio_i2s

PATH = "/test.wav"
TYPE = 0  # 0 = continuous, 1 = single buffer

with adafruit_wave.open(PATH) as file:
    codec = pio_i2s.I2S(
        bit_clock=board.GP0,  # word select is GP1
        data_out=board.GP3,
        channel_count=file.getnchannels(),
        sample_rate=file.getframerate(),
        bits_per_sample=file.getsampwidth() * 8,
        samples_signed=True,
        buffer_size=1024,
    )

    if not TYPE:
        """Example using continuous file operations"""

        while data := memoryview(file.readframes(codec.buffer_size)).cast(codec.buffer_format):
            codec.write(data)  # blocking

    else:
        """Example using a single large buffer"""

        MAX_LENGTH = 3000

        # Load audio data
        data = memoryview(
            file.readframes(MAX_LENGTH / 1000 * file.getframerate() * file.getnchannels())
        ).cast(codec.buffer_format)

        # Play audio data, this is blocking
        codec.play(data)

    # Stop I2S bus
    codec.deinit()
