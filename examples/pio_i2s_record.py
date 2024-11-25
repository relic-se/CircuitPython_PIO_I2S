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
LENGTH = 3000  # ms

mic = pio_i2s.I2S(
    bit_clock=board.GP0,  # word select is GP1
    data_in=board.GP2,
    channel_count=1,
    sample_rate=22050,
    bits_per_sample=16,
    samples_signed=True,
    buffer_size=16384,  # must be big enough to avoid delays due to file operations
)

# Remove existing file if it exists
try:
    os.remove(PATH)
except OSError:
    pass

# Determine the number of buffers we need to write
num_buffers = int((LENGTH / 1000.0 * mic.sample_rate * mic.channel_count) // mic.buffer_size)

# Read audio data from i2s bus and write to wave file
with adafruit_wave.open(PATH, mode="wb") as file:
    file.setframerate(mic.sample_rate)
    file.setnchannels(mic.channel_count)
    file.setsampwidth(mic.bits_per_sample // 8)
    for i in range(num_buffers):
        file.writeframes(mic.read(block=True))

# Stop microphone
mic.deinit()
