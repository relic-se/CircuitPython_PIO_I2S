# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import board
import ulab.numpy as np

import pio_i2s

codec = pio_i2s.I2S(
    bit_clock=board.GP1,
    word_select=board.GP2,  # does not need to be sequential in peripheral mode
    data_in=board.GP0,  # must come before bit_clock
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
