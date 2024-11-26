# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

# boot.py:
# import storage
# storage.remount("/", readonly=False)

import array
import os

import adafruit_wave
import board

import pio_i2s

PATH = "/test.wav"
TYPE = 0  # 0 = continuous, 1 = single buffer
LENGTH = (
    3000 if not TYPE else 2000
)  # ms, size may be limited depending on available RAM if using single buffer mode

mic = pio_i2s.I2S(
    bit_clock=board.GP0,  # word select is GP1
    data_in=board.GP2,
    channel_count=1,
    sample_rate=22050,
    bits_per_sample=16,
    samples_signed=True,
    buffer_size=16384
    if not TYPE
    else 1024,  # must be big enough to avoid delays if using continuous file operations
)

# Remove existing file if it exists
try:
    os.remove(PATH)
except OSError:
    pass

if not TYPE:
    """Example using continuous file operations"""

    # Determine the number of buffers we need to write
    num_buffers = int((LENGTH / 1000.0 * mic.sample_rate * mic.channel_count) // mic.buffer_size)

    # Read audio data from i2s bus and write to wav file
    with adafruit_wave.open(PATH, mode="wb") as file:
        file.setframerate(mic.sample_rate)
        file.setnchannels(mic.channel_count)
        file.setsampwidth(mic.bits_per_sample // 8)
        for i in range(num_buffers):
            file.writeframes(mic.read(block=True))

else:
    """Example using a single large buffer"""

    # Generate buffer of desired length
    data = array.array(
        mic.buffer_format, [0] * int(LENGTH / 1000 * mic.sample_rate * mic.channel_count)
    )

    # Fill buffer with samples from microphone, this is blocking
    mic.record(data)

    # Write samples to wav file
    with adafruit_wave.open(PATH, mode="wb") as file:
        file.setframerate(mic.sample_rate)
        file.setnchannels(mic.channel_count)
        file.setsampwidth(mic.bits_per_sample // 8)
        file.writeframes(data)

# Stop microphone
mic.deinit()
