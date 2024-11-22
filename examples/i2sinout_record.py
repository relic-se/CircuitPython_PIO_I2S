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

import i2sinout

PATH = "/test.wav"
LENGTH = 1000  # ms

mic = i2sinout.I2SInOut(
    bit_clock=board.GP0,  # word select is GP1
    data_in=board.GP2,
    channel_count=1,
    sample_rate=22050,
    bits_per_sample=16,
    samples_signed=True,
    buffer_size=1024,
)

# Remove existing file if it exists
try:
    os.remove(PATH)
except OSError:
    pass

# Determine the number of buffers we need to write
num_buffers = int((LENGTH / 1000.0 * mic.sample_rate * mic.channel_count) // mic.buffer_size)

# Copy audio from input buffer into file buffer
# NOTE: Recording data and writing to a file at the same time causes stutters in audio
data = array.array(mic.buffer_format, [0] * mic.buffer_size * num_buffers)
for i in range(num_buffers):
    buffer = mic.read(block=True)
    for j in range(mic.buffer_size):
        data[i * mic.buffer_size + j] = buffer[j]

# Stop microphone
mic.deinit()

# Write audio data to wave file
with adafruit_wave.open(PATH, mode="wb") as file:
    file.setframerate(mic.sample_rate)
    file.setnchannels(mic.channel_count)
    file.setsampwidth(mic.bits_per_sample // 8)
    file.writeframes(data)
