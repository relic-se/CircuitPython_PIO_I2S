# SPDX-FileCopyrightText: Copyright (c) 2024 Cooper Dalrymple
#
# SPDX-License-Identifier: Unlicense

import array

import audiobusio
import audiocore
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

input = i2sinout.I2SInOut(
    peripheral=True,  # Share clock signals with I2SOut
    data_in=board.GP0,
    bit_clock=board.GP1,
    word_select=board.GP2,
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

mixer = audiomixer.Mixer(
    voice_count=1,
    buffer_size=BUFFER_SIZE,
    **properties,
)

# Currently unable to get buffer from audio sample objects to feed into I2SInOut
# Must use a separate `audiosample.I2SOut` object, and connect bit_clock and word_select together
output = audiobusio.I2SOut(
    bit_clock=board.GP3,
    word_select=board.GP4,
    data=board.GP5,
)
output.play(mixer)

try:
    import audiodelays

    effect = audiodelays.Echo(
        buffer_size=BUFFER_SIZE,
        **properties,
    )
    effect.play(sample, loop=True)
    mixer.voice[0].play(effect)
except ImportError:
    mixer.voice[0].play(sample, loop=True)

while True:
    # Load RawSample buffer with I2S input data
    data = input.read()
    for i in range(BUFFER_SIZE):
        sample_buffer[i] = data[i]
