import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from .camera import capture
from .file_structure import iso_datetime_for_filename
from .prepare import create_file_structure_for_experiment, get_experiment_configuration, hostname_is_correct
from .storage import free_space_for_one_image, how_many_images_with_free_space
from .sync_manager import end_syncing_process, sync_directory_in_separate_process

from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-5.5s]--- %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler("experiment.log", mode='a', maxBytes=10*1024*1024, backupCount=2, encoding=None, delay=0)
    ]
)


def perform_experiment(configuration):
    '''Perform experiment using settings passed in through the configuration.
       experimental configuration defines the capture frequency and duration of the experiment
       as well as controlling the camera settings to be used to capture images.
       Experimental output directories are created prior to initiating image capture and
       experimental metadata is collected during the experiment and saved.
       Finally, imagery and experimental metadata is synced to s3 on an ongoing basis.
     Args:
        configuration: ExperimentConfiguration instance. Determines how the experiment should be performed.
     Returns:
        None

     Notes on local development:
       There is a helper function to simulate a capture of a file by copying it into
       the location a capture would place a file.  You can use it by changing the from
       from camera import capture => from camera import capture, simulate_capture_with_copy
       and using simulate_capture_with_copy instead of capture.
    '''

    # print out warning that no duration has been set and inform how many
    # estimated images can be stored
    if configuration.duration is None:
        how_many_images_can_be_captured = how_many_images_with_free_space()
        logging.info('No experimental duration provided.')
        logging.info(f'Number of images that can be captured with free space: {how_many_images_can_be_captured}')

    # Initial value of start_date results in immediate capture on first iteration in while loop
    next_capture_time = configuration.start_date

    while configuration.duration is None or datetime.now() < configuration.end_date:
        if datetime.now() < next_capture_time:
            time.sleep(0.1)  # No need to totally peg the CPU
            continue

        # next_capture_time is agnostic to the time needed for capture and writing of image
        next_capture_time = next_capture_time + timedelta(seconds=configuration.interval)

        # iterate through each capture variant and capture an image with it's settings
        for variant in configuration.variants:

            if not free_space_for_one_image():
                end_experiment(
                    configuration,
                    experiment_ended_message='Insufficient space to save the image. Quitting...'
                )

            iso_ish_datetime = iso_datetime_for_filename(datetime.now())
            capture_params_for_filename = variant.capture_params.replace('-', '').replace(' ', '_')
            image_filename = f'{iso_ish_datetime}{capture_params_for_filename}.jpeg'
            image_filepath = os.path.join(configuration.experiment_directory_path, image_filename)

            capture(image_filepath, additional_capture_params=variant.capture_params)

            # If a sync is currently occuring, this is a no-op.
            if not configuration.skip_sync:
                sync_directory_in_separate_process(configuration.experiment_directory_path)

    end_experiment(configuration, experiment_ended_message='Experiment completed successfully!')


def end_experiment(experiment_configuration, experiment_ended_message):
    ''' Complete an experiment by ensuring all remaining images finish syncing '''
    # If a file(s) is written after a sync process begins it does not get added to the list to sync.
    # This is fine during an experiment, but at the end of the experiment, we want to make sure to sync all the
    # remaining images. To that end, we end any existing sync process and start a new one
    logging.info(experiment_ended_message)
    logging.info("Beginning final sync to s3 due to end of experiment...")
    if not experiment_configuration.skip_sync:
        end_syncing_process()
        sync_directory_in_separate_process(experiment_configuration.experiment_directory_path, wait_for_finish=True)
    logging.info("Final sync to s3 completed!")
    quit()


def run_experiment(cli_args=None):
    ''' Top-level function to run an experiment.
    Collects command-line arguments, captures images, and syncs them to s3.
    Also checks that the system has the correct hostname configured and handles graceful closure upon KeyboardInterrupt.

    Args:
        cli_args: Optional: list of command-line argument strings like sys.argv. If not provided, sys.argv will be used
    Returns:
        None
    '''
    try:
        if cli_args is None:
            # First argument is the name of the command itself, not an "argument" we want to parse
            cli_args = sys.argv[1:]
        configuration = get_experiment_configuration(cli_args)

        if not hostname_is_correct(configuration.hostname):
            quit_message = f'"{configuration.hostname}" is not a valid hostname.'
            quit_message += ' Contact your local dev for instructions on setting a valid hostname.'
            logging.error(quit_message)
            quit()

        create_file_structure_for_experiment(configuration)

        try:
            perform_experiment(configuration)
        except KeyboardInterrupt:
            end_experiment(configuration, experiment_ended_message='Keyboard interrupt detected. Quitting...')

    # The Exception used here is generic due to check_call (which calls raspistill/s3 sync) raises a SubprocessError
    # exception if there is an error.  Additionally, there may be other Exception types that we want to catch as well
    # that we are not aware of and that can be illuminated by using a generic Exception type
    except Exception as exception:
        logging.error("Unexpected exception occurred")
        logging.error(exception)


if __name__ == '__main__':
    print('Please call "run_experiment" instead of "python experiment.py"')
