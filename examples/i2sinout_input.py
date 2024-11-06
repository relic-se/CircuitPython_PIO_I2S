# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import board
import i2sinout
import ulab.numpy as np

codec = i2sinout.I2SInOut(
    bit_clock=board.GP0, # word select is GP1
    data_in=board.GP2,
    channel_count=1,
    sample_rate=22050,
    bits_per_sample=16,
    samples_signed=True,
    buffer_size=1024,
)

while True:
    if data := codec.read():
        print(np.max(np.array(data, dtype=np.int16)))
