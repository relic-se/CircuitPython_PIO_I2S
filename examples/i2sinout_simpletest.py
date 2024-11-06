# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import board
import i2sinout

codec = i2sinout.I2SInOut(
    bit_clock=board.GP0,  # word select is GP1
    data_out=board.GP2,
    data_in=board.GP3,
    sample_rate=22050,
)

while True:
    codec.write(codec.read())
