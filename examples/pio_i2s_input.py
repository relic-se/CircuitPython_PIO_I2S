# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import board
import ulab.numpy as np

import pio_i2s

codec = pio_i2s.I2S(
    bit_clock=board.GP0,  # word select is GP1
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
