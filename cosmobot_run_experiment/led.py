import sys
import argparse

#  Import pattern to support development without needing pi specific modules installed.
#  board and neopixel modules have been stubbed out within "pi_stubs" folder
try:
    import board  # noqa: E0401
    import neopixel  # noqa: E0401
except ImportError:
    from .pi_stubs import board, neopixel

NUMBER_OF_LEDS = 16
ALL_PIXELS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
ONE_PIXEL = [1]  # By request of Jacob, legacy data used this index
DEFAULT_PIXEL_ORDER = (1, 0, 2, 3)

NAMED_COLORS_IN_RGB = {
    'white': (0, 0, 0, 255), 'blue': (0, 0, 255, 0), 'red': (255, 0, 0, 0),
    'purple': (255, 0, 255, 0), 'green': (0, 255, 0, 0)
}


def _show_pixels(color, intensity, pixel_indices=ALL_PIXELS):
    '''Update led pixel color & intensity
     Args:
        color: 4-tuple rgbw
        intensity: led intensity within the range 0.0 (off) to 1.0 (full intensity)
        pixel_indices: list of pixel indices to update color and intensity
     Returns:
        None
    '''

    pixels = neopixel.NeoPixel(
        board.D18,
        NUMBER_OF_LEDS,
        brightness=intensity,
        pixel_order=DEFAULT_PIXEL_ORDER
    )

    for pixel_index in pixel_indices:
        pixels[pixel_index] = color


def set_led(cli_args=None):
    '''Extract and verify arguments passed in from the command line for controlling leds
     Args:
        args: list of command-line-like argument strings such as sys.argv
     Returns:
        dictionary of arguments parsed from the command line
    '''

    if cli_args is None:
        # First argument is the name of the command itself, not an "argument" we want to parse
        cli_args = sys.argv[1:]

    arg_parser = argparse.ArgumentParser(description='''
        Example Usage:
        ALL LEDS:  set_led --intensity 0.8 --color white
        ONE LED:   set_led --intensity 0.8 --color white --one_led
        OFF:       set_led --intensity 0.0
    ''')

    arg_parser.add_argument('--intensity', required=False, type=float, default=0.0, help='led intensity (0.0 - 1.0)')
    arg_parser.add_argument(
        '--color', required=False, type=str, default='white',
        help='Named color', choices=NAMED_COLORS_IN_RGB.keys()
    )
    arg_parser.add_argument('--one-led', required=False, action='store_true', help='led intensity (0.0 - 1.0)')

    # In order to support usage of this function from another module (not directly from the console script),
    # parse_known_args and arg namespace is used to only utilize args that we care about in the led module.
    led_arg_namespace, _ = arg_parser.parse_known_args(cli_args)
    args = vars(led_arg_namespace)

    pixel_indices = ONE_PIXEL if args['one_led'] else ALL_PIXELS

    _show_pixels(NAMED_COLORS_IN_RGB[args['color']], args['intensity'], pixel_indices=pixel_indices)