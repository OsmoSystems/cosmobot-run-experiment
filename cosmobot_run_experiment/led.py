import sys
import argparse

try:
    import board  # noqa: E0401
    import neopixel  # noqa: E0401
except ImportError:
    from .dummy import board, neopixel

NUMBER_OF_LEDS = 16
ALL_PIXELS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
DEFAULT_PIXEL_ORDER = (1, 0, 2, 3)

NAMED_COLORS_IN_RGB = {
    'white': (0, 0, 0, 255), 'blue': (0, 0, 255, 0), 'red': (0, 0, 255, 0),
    'purple': (255, 0, 255, 0), 'green': (0, 255, 0, 0)
}


def _show_pixels(color, intensity, pixel_indices=ALL_PIXELS):
    pixels = neopixel.NeoPixel(
        board.D18,
        NUMBER_OF_LEDS,
        brightness=intensity,
        pixel_order=DEFAULT_PIXEL_ORDER
    )

    for pixel_index in pixel_indices:
        pixels[pixel_index].fill(color)
        pixels[pixel_index].show()


def set_led(cli_args=None):
    if cli_args is None:
        # First argument is the name of the command itself, not an "argument" we want to parse
        cli_args = sys.argv[1:]

    arg_parser = argparse.ArgumentParser(description='''
        Example Usage:
        set_led --intensity 0.8 --color white
    ''')

    arg_parser.add_argument('--intensity', required=False, type=float, default=1.0, help='led intensity (0.0 - 1.0)')
    arg_parser.add_argument(
        '--color', required=False, type=str, default='white',
        help='Named color', choices=NAMED_COLORS_IN_RGB.keys()
    )

    args = vars(arg_parser.parse_args(cli_args))
    _show_pixels(NAMED_COLORS_IN_RGB[args['color']], args['intensity'])
