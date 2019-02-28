import sys
import argparse
import logging

#  Import pattern to support development without needing pi specific modules installed.
#  board and neopixel modules have been stubbed out within "pi_stubs" folder
try:
    import board  # noqa: E0401  Unable to import
    import neopixel  # noqa: E0401  Unable to import
except ImportError:
    print("Unable to import pi specific modules to control leds")
    print("Using stubbed out board & neopixel modules instead")
    from .pi_stubs import board, neopixel

NUMBER_OF_LEDS = 16
ALL_PIXELS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
ONE_PIXEL = [1]  # By request of Jacob, legacy data used this index

# Specifies the order in which color values from a color tuple are applied
# Default is GRB, we explicitly set it to RGB.
RGB_PIXEL_ORDER = neopixel.GRB

NAMED_COLORS_IN_RGBW = {
    'white': (255, 255, 255),
    'blue': (0, 0, 255),
    'red': (255, 0, 0),
    'purple': (255, 0, 255),
    'green': (0, 255, 0)
}


def show_pixels(color=NAMED_COLORS_IN_RGBW['white'], intensity=1, use_one_led=False):
    '''Update led pixel color & intensity of the pixel_indices that are passed in
     Args:
        color: 3-tuple RGB
        intensity: led intensity within the range 0.0 (off) to 1.0 (full intensity)
        pixel_indices: list of pixel indices to update color and intensity
     Returns:
        None
    '''

    pixel_indices = ONE_PIXEL if use_one_led else ALL_PIXELS

    pixels = neopixel.NeoPixel(
        board.D18,
        NUMBER_OF_LEDS,
        brightness=intensity,
        pixel_order=RGB_PIXEL_ORDER
    )

    for pixel_index in pixel_indices:
        pixels[pixel_index] = color

    try:
        pixels.show()
    except (
        AttributeError,  # happens in local development without the picamera library installed
        ValueError,  # happens on a pi when a board pin is misconfigured/seated
    ) as exception:
        logging.error("Exception occurred while setting led.  Is the led connected correctly?")
        logging.error(exception)
        pass


def turn_off_leds():
    show_pixels(intensity=0)


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
    arg_parser.add_argument('--color', required=True, type=str, help='Named color', choices=NAMED_COLORS_IN_RGBW.keys())
    arg_parser.add_argument('--intensity', required=False, type=float, default=0.0, help='led intensity (0.0 - 1.0)')
    arg_parser.add_argument(
        '--use-one-led', required=False, action='store_true',
        help='If provided, change one LED (default: all LEDs)'
    )

    args = vars(arg_parser.parse_args(cli_args))

    # To avoid complicated states, always turn off LEDs before setting them
    turn_off_leds()
    show_pixels(
        color=NAMED_COLORS_IN_RGBW[args['color']],
        intensity=args['intensity'],
        use_one_led=args['use_one_led']
    )
