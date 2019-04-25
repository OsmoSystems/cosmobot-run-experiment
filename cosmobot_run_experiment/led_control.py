import argparse
import logging
import sys

#  Import pattern to support development without needing pi specific modules installed.
#  board and neopixel modules have been stubbed out within "pi_stubs" folder
try:
    import board  # noqa: E0401  Unable to import
    import digitalio  # noqa: E0401  Unable to import
    import neopixel  # noqa: E0401  Unable to import
except ImportError:
    print('''
        Unable to import pi specific modules to control leds
        Using stubbed out modules instead
    ''')
    from cosmobot_run_experiment.pi_stubs import board, neopixel, digitalio

NUMBER_OF_LEDS = 16
ALL_PIXELS = list(range(NUMBER_OF_LEDS))
ONE_PIXEL = [0]

DIGITAL_LED_PIN = board.D6
NEOPIXEL_PIN = board.D10


NAMED_COLORS_IN_RGB = {
    'white': (255, 255, 255),
    'blue': (0, 0, 255),
    'red': (255, 0, 0),
    'purple': (255, 0, 255),
    'green': (0, 255, 0)
}

# The NeoPixel library takes out a lock on the physical pin so we can't just generate more as needed.
# Thus we use this singleton, global NeoPixel object
# See Section 5.2 of these docs for more detail on the NeoPixel class:
# https://buildmedia.readthedocs.org/media/pdf/adafruit-circuitpython-neopixel/latest/adafruit-circuitpython-neopixel.pdf
pixels = neopixel.NeoPixel(
    pin=NEOPIXEL_PIN,
    n=NUMBER_OF_LEDS,
    brightness=1.0,
    # According to the docs, neopixel.GRBW should be the default, but in testing the default appears to be neopixel.GRB
    # Explicitly set just to be sure. If NeoPixel includes a white LED, set to neopixel.GRBW
    pixel_order=neopixel.GRB
)


def _adjust_color_intensity(color_tuple, intensity):
    '''Adjust color tuple values by an intensity value
        There is no method for setting led intensity after initialization of a neopixel object
        and since there is resource/hardware management to consider when initializating/deinitializating
        a neopixel object that present edge cases, we use a more simple approach by adjusting the intensity of each
        color channel in the color_tuple.
    Args:
        color: 3-tuple RGB
        intensity: led intensity within the range 0.0 (off) to 1.0 (full intensity)
    Returns:
        color_tuple with each value multiplied by intensity
    '''
    return tuple(int(intensity*color_channel) for color_channel in color_tuple)


def _control_neopixel_leds(color=NAMED_COLORS_IN_RGB['white'], intensity=1, use_one_led=False):
    '''Control 16-pixel NeoPixel LED array intensity and color.
    '''
    global pixels

    pixel_indices = ONE_PIXEL if use_one_led else ALL_PIXELS

    if not isinstance(color, tuple) or len(color) != 3:
        raise ValueError('color should be a 3-tuple RGB but was {color}'.format(**locals()))

    intensity_adjusted_color = _adjust_color_intensity(color, intensity)

    for pixel_index in pixel_indices:
        # Since the default is auto_write=True, LEDs get updated immediately
        pixels[pixel_index] = intensity_adjusted_color


def _control_digitalio_led(on=True):
    '''Turn on/off Digital IO LED.
    '''
    led = digitalio.DigitalInOut(pin=DIGITAL_LED_PIN)
    led.direction = digitalio.Direction.OUTPUT
    led.value = on


def control_leds(color=NAMED_COLORS_IN_RGB['white'], intensity=1, use_one_led=False):
    '''
    Control 16-pixel NeoPixel LED array intensity and color.
    Simultaneously turn on/off Digital IO LED anytime intensity > 0. (No color control)

    Args:
        color: 3-tuple RGB
        intensity: led intensity within the range 0.0 (off) to 1.0 (full intensity)
        use_one_led: Optional (default=False). If True, only NeoPixel LED at index 0 will be used and all other
            NeoPixels will be turned off. If False, all 16 NeoPixels will be controlled.
    Returns:
        None
    '''
    led_name = 'LED' if use_one_led else 'LEDs'
    logging.info('Setting {led_name} to color {color}, intensity {intensity}'.format(**locals()))

    _control_neopixel_leds(color, intensity, use_one_led)
    _control_digitalio_led(on=intensity > 0)


def set_led(cli_args=None, pass_through_unused_args=False):
    '''Extract and verify arguments passed in from the command line for controlling leds
     Args:
        args: list of command-line-like argument strings such as sys.argv
     Returns:
        None
    '''

    if cli_args is None:
        # First argument is the name of the command itself, not an "argument" we want to parse
        cli_args = sys.argv[1:]

    arg_parser = argparse.ArgumentParser(description='''
        Example Usage:
        ALL LEDS:  set_led --intensity 0.8 --color white
        ONE LED:   set_led --intensity 0.8 --color white --use-one-led
        OFF:       set_led --intensity 0.0
    ''')

    # Specify color to be required to trigger help display (no help is shown if no args are required)
    arg_parser.add_argument(
        '--color',
        required=True,
        type=str,
        help='Named color (Required)',
        choices=NAMED_COLORS_IN_RGB.keys()
    )
    arg_parser.add_argument(
        '--intensity',
        required=False,
        type=float,
        default=0.0,
        help='LED intensity [0.0 - 1.0].  (Optional) Default is 0.0 (off)'
    )
    arg_parser.add_argument(
        '--use-one-led',
        required=False,
        action='store_true',
        help='If provided, change one LED. (Optional) Default changes all LEDs'
    )

    args = vars(arg_parser.parse_args(cli_args))

    control_leds(
        color=NAMED_COLORS_IN_RGB[args['color']],
        intensity=args['intensity'],
        use_one_led=args['use_one_led']
    )
