from itertools import chain
from functools import partial
import os

import pandas as pd
import numpy as np

from osmo_camera.get_files import get_files_with_extension
from osmo_camera.select_ROI import get_ROIs_for_image
from osmo_camera import dng


# Running numpy calculations against this axis aggregates over the image for each channel, as color channels are axis=2
IMAGE_AXES = (0, 1)


ROI_STATISTIC_CALCULATORS = {
    'mean': partial(np.mean, axis=IMAGE_AXES),
    'median': partial(np.median, axis=IMAGE_AXES),
    'min': partial(np.amin, axis=IMAGE_AXES),
    'max': partial(np.amax, axis=IMAGE_AXES),
    'stdev': partial(np.std, axis=IMAGE_AXES),
    **{
        f'percentile_{percentile}': partial(np.percentile, q=percentile, axis=IMAGE_AXES)
        for percentile in [99, 95, 90, 75, 50, 25]
    }
}


def _process_ROI(ROI):
    channel_stats = {
        stat_name: stat_calculator(ROI)
        for stat_name, stat_calculator in ROI_STATISTIC_CALCULATORS.items()
    }

    flattened_channel_stats = {
        f'{color}_{stat}': channel_stats[stat][color_index]
        for stat in channel_stats
        for color_index, color in enumerate('rgb')  # TODO: is it a safe assumption that everything's in rgb??
    }

    return flattened_channel_stats


def process_image(dng_image_path, ROI_definitions):
    ''' Process all the ROIs in a single image into summary statistics

    1. Convert JPEG+RAW -> .DNG
    2. For each ROI:
        a. Crop
        b. Calculate summary stats

    Args:
        dng_image_path: The full file path of a DNG image.
        ROI_definitions: Definitions of Regions of Interest (ROIs) to summarize. A map of {ROI_name: ROI_definition}
        Where ROI_definition is a 4-tuple in the format provided by cv2.selectROI: (start_col, start_row, cols, rows)

    Returns:
        An array of summary statistics dictionaries - one for each ROI
    '''
    rgb_image = dng.open.as_rgb(dng_image_path)

    ROIs = get_ROIs_for_image(rgb_image, ROI_definitions)

    return [
        {
            'timestamp': dng.metadata.capture_date(dng_image_path),
            'image': os.path.basename(dng_image_path),
            'ROI': ROI_name,
            'ROI definition': ROI_definitions[ROI_name],
            **_process_ROI(ROI)
        }
        for ROI_name, ROI in ROIs.items()
    ]


def process_images(dng_images_dir, ROI_definitions):
    ''' Process all images in a given directory

    Args:
        dng_images_dir: The directory of images to process. Assumes images have already been converted to .DNGs
        ROI_definitions: Definitions of Regions of Interest (ROIs) to summarize. A map of {ROI_name: ROI_definition}
        Where ROI_definition is a 4-tuple in the format provided by cv2.selectROI: (start_col, start_row, cols, rows)

    Returns:
        An pandas DataFrame in which each row contains summary statistics for a single ROI in a single image
    '''

    dng_image_paths = sorted(get_files_with_extension(dng_images_dir, '.dng'))

    summary_statistics = pd.DataFrame(
        # Flatten all ROI summaries for all images into a single 1D list
        list(chain.from_iterable([
            process_image(dng_image_path, ROI_definitions)
            for dng_image_path in dng_image_paths
        ]))
    ).sort_values('timestamp').reset_index(drop=True)

    return summary_statistics
