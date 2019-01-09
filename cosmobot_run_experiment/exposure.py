import os
import sys
import argparse
import numpy as np
from .file_structure import get_files_with_extension
from .open import as_rgb

COLOR_CHANNELS = 'rgb'
COLOR_CHANNEL_COUNT = len(COLOR_CHANNELS)


def _generate_statistics(rgb_image, overexposed_threshold=0.99, underexposed_threshold=0.01):
    ''' Generate pixel percentage overexposure & underexposure of entire image and overexposure pixel percentage by
        color channel

    Args:
        rgb_image: a `RGB Image`
        overexposed_threshold: threshold at which a color's intensity is overexposed
        underexposed_threshold: threshold at which a color's intensity is underexposed
    Returns:
        dictionary of overexposure & underexposure statistics
    '''

    overexposed_pixel_count_by_channel = (rgb_image > overexposed_threshold).sum(axis=(0, 1))
    underexposed_pixel_count_by_channel = (rgb_image < underexposed_threshold).sum(axis=(0, 1))
    per_channel_pixel_count = rgb_image.size / COLOR_CHANNEL_COUNT

    return {
        'overexposed_threshold': overexposed_threshold,
        'underexposed_threshold': underexposed_threshold,
        'overexposed_percent': (rgb_image > overexposed_threshold).sum() / rgb_image.size,
        'underexposed_percent': (rgb_image < underexposed_threshold).sum() / rgb_image.size,
        ** {
            'overexposed_percent_{}'.format(color):
                overexposed_pixel_count_by_channel[color_index] / per_channel_pixel_count
            for color_index, color in enumerate(COLOR_CHANNELS)
        },
        ** {
            'underexposed_percent_{}'.format(color):
                underexposed_pixel_count_by_channel[color_index] / per_channel_pixel_count
            for color_index, color in enumerate(COLOR_CHANNELS)
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
        The --directory flag specifies the directory that contains the images to generate exposure statstics from

        Example Usage:
        review_exposure --directory /Users/osmo/cosmobot-data-sets/directory_of_images_to_generate_exposure_stats_from
    ''')

    arg_parser.add_argument('--directory', required=True, type=str, help='directory to use to review image exposures')
    args = vars(arg_parser.parse_args(cli_args))
    review_exposure_statistics(args['directory'])
