import os
import sys
import argparse
from .file_structure import get_files_with_extension
from .open import as_rgb

COLOR_CHANNEL_COUNT = 3


def _generate_statistics(rgb_image, overexposed_threshold = 0.99, underexposed_threshold = 0.01):
    return {
        'overexposed_percent': (rgb_image > overexposed_threshold).sum() / rgb_image.size,
        'underexposed_percent': (rgb_image < underexposed_threshold).sum() / rgb_image.size,
        ** { # overexposure percent by color channel
            'overexposed_percent_{}'.format(color):
                (rgb_image[:, :, color_index] > overexposed_threshold).sum() / (rgb_image.size / COLOR_CHANNEL_COUNT)
            for color_index, color in enumerate('rgb')
        }
    }


def review_exposure_statistics(experiment_directory_path):
    print("Reviewing exposure settings:")
    image_paths = get_files_with_extension(experiment_directory_path, '.jpeg')

    for index, image_path in enumerate(image_paths):
        rgb_image = as_rgb(os.path.join(experiment_directory_path, image_path))
        print("({}/{}) - {}".format(index + 1, len(image_paths), image_path))
        print(_generate_statistics(rgb_image))


def review_exposure(cli_args=None):
    if cli_args is None:
        # First argument is the name of the command itself, not an "argument" we want to parse
        cli_args = sys.argv[1:]

    arg_parser = argparse.ArgumentParser(description='''
        TODO:
    ''')

    arg_parser.add_argument('--directory', required=True, type=str, help='directory to review image exposures')
    args = vars(arg_parser.parse_args(cli_args))
    review_exposure_statistics(args['directory'])
