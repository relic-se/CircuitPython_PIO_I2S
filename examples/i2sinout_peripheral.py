# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import board
import ulab.numpy as np

import i2sinout

codec = i2sinout.I2SInOut(
    bit_clock=board.GP0,
    word_select=board.GP1,  # does not need to be sequential in peripheral mode
    data_in=board.GP2,
    channel_count=1,
    sample_rate=22050,
    bits_per_sample=16,
    samples_signed=True,
    buffer_size=1024,
    peripheral=True,
)

while True:
    if data := codec.read():
        print(np.max(np.array(data, dtype=np.int16)))
