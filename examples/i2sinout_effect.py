# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import array

import audiobusio
import audiocore
import audiodelays
import audiomixer
import board

import i2sinout

BUFFER_SIZE = 1024

properties = {
    "channel_count": 2,
    "sample_rate": 22050,
    "bits_per_sample": 16,
    "samples_signed": True,
}

bit_clock_pin = board.GP0
word_select_pin = board.GP1

input = i2sinout.I2SInOut(
    peripheral=True,  # Share clock signals with I2SOut
    bit_clock=bit_clock_pin,
    word_select=word_select_pin,
    data_in=board.GP2,
    buffer_size=BUFFER_SIZE,
    **properties,
)

sample_buffer = array.array(input.buffer_format, [0] * BUFFER_SIZE)
sample = audiocore.RawSample(
    buffer=sample_buffer,
    channel_count=properties["channel_count"],
    sample_rate=properties["sample_rate"],
    single_buffer=False,  # double-buffer is required to update buffer properly
)

effect = audiodelays.Echo(
    buffer_size=BUFFER_SIZE,
    **properties,
)
effect.play(sample, loop=True)

mixer = audiomixer.Mixer(
    voice_count=1,
    buffer_size=BUFFER_SIZE,
    **properties,
)
mixer.play(effect)

# Currently unable to get buffer from audio sample objects to feed into I2SInOut
# Must use a separate `audiosample.I2SOut` object
output = audiobusio.I2SOut(
    bit_clock=bit_clock_pin,  # Share clock signal pins with I2SInOut
    word_select=word_select_pin,
    data=board.GP5,
)
output.play(mixer)

while True:
    # Load RawSample buffer with I2S input data
    data = input.read()
    for i in len(BUFFER_SIZE):
        sample_buffer[i] = data[i]
