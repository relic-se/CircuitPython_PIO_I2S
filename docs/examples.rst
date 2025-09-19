Simple test
-----------

Ensure your device works with this simple test.

.. literalinclude:: ../examples/pio_i2s_simpletest.py
    :caption: examples/pio_i2s_simpletest.py
    :linenos:

Audio Input
-----------

Monitor the level of an incoming audio stream over I2S.

.. literalinclude:: ../examples/pio_i2s_input.py
    :caption: examples/pio_i2s_input.py
    :linenos:

Audio Output
------------

Generate a sine wave and output it through the I2S bus concurrently using buffer looping.

.. literalinclude:: ../examples/pio_i2s_output.py
    :caption: examples/pio_i2s_output.py
    :linenos:

Peripheral Input
----------------

Monitor the level of an incoming audio stream over I2S acting as a peripheral device.

.. literalinclude:: ../examples/pio_i2s_peripheral.py
    :caption: examples/pio_i2s_peripheral.py
    :linenos:

Playing WAV File
----------------

Demonstration of WAV file playback using continuous or single buffer methods.

.. literalinclude:: ../examples/pio_i2s_play.py
    :caption: examples/pio_i2s_play.py
    :linenos:

Recording to WAV File
---------------------

Demonstration of recording audio to WAV file using continuous or single buffer methods.

.. literalinclude:: ../examples/pio_i2s_record.py
    :caption: examples/pio_i2s_record.py
    :linenos:

Realtime Audio Effect
---------------------

Demonstration of using independent I2S input and output buses and an :class:`audiocore.RawSample`
object to apply audio effects to an audio data stream.

.. literalinclude:: ../examples/pio_i2s_effect.py
    :caption: examples/pio_i2s_effect.py
    :linenos:
