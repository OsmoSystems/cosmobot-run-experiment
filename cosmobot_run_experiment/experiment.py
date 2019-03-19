import os
import sys
import time
import logging
import traceback

from .camera import simulate_capture_with_copy as capture
from .file_structure import iso_datetime_for_filename, remove_experiment_directory
from .prepare import create_file_structure_for_experiment, get_experiment_configuration, hostname_is_correct
from .storage import free_space_for_one_image, how_many_images_with_free_space
from .sync_manager import end_syncing_process, sync_directory_in_separate_process
from .exposure import review_exposure_statistics
from .led_control import set_led
from .temperature import read_temperature, create_temperature_log, log_temperature_at_capture

from datetime import datetime, timedelta

# Basic logging configuration - sets the base log level to INFO and provides a
# log format (time, log level, log message) for all messages to be written to stdout (console)
# or to a log file. This is set outside of a function as the execution path through testing
# shows that setting the values inside a function causes some silent failure with stdout to a console.
logging_format = "%(asctime)s [%(levelname)s]--- %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=logging_format,
    handlers=[
        logging.StreamHandler()
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
        logging.info('Estimated number of images that can be captured with free space: '
                     '{how_many_images_can_be_captured}'.format(**locals()))

    # Initial value of start_date results in immediate capture on first iteration in while loop
    next_capture_time = configuration.start_date

    # create temperature.csv with headers in experiment directory
    create_temperature_log(configuration.experiment_directory_path)

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

            show_pixels(
                NAMED_COLORS_IN_RGB[variant.led_color],
                variant.led_intensity,
                use_one_led=variant.use_one_led
            )

            time.sleep(variant.led_warm_up)

            iso_ish_datetime = iso_datetime_for_filename(datetime.now())
            capture_params_for_filename = variant.capture_params.replace('-', '').replace(' ', '_')
            image_filename = '{iso_ish_datetime}_{capture_params_for_filename}_.jpeg'.format(**locals())
            image_filepath = os.path.join(configuration.experiment_directory_path, image_filename)

            temperature_before_capture = read_temperature()
            capture(image_filepath, additional_capture_params=variant.capture_params)
            temperature_after_capture = read_temperature()

            log_temperature_at_capture(
                configuration.experiment_directory_path,
                image_filename,
                temperature_before_capture,
                temperature_after_capture
            )

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

    if not experiment_configuration.skip_sync:
        logging.info("Beginning final sync to s3 due to end of experiment...")
        end_syncing_process()
        sync_directory_in_separate_process(
            experiment_configuration.experiment_directory_path,
            wait_for_finish=True,
            exclude_log_files=False,
            erase_synced_files=experiment_configuration.erase_synced_files
        )
        logging.info("Final sync to s3 completed!")

        # s3 mv does not remove a directory so we have to do it here after mv is complete
        if experiment_configuration.erase_synced_files:
            remove_experiment_directory(experiment_configuration.experiment_directory_path)

    if experiment_configuration.review_exposure:
        review_exposure_statistics(experiment_configuration.experiment_directory_path)

    quit()


def set_up_log_file_with_base_handler(experiment_directory):
    log_filepath = os.path.join(experiment_directory, 'experiment.log')
    log_file_handler = logging.FileHandler(log_filepath)
    formatter = logging.Formatter(logging_format)
    log_file_handler.setFormatter(formatter)

    # Retrieve the root logger object that the module level logging.[loglevel] object uses
    # and adds the additional "log to file" handler.  This is similar to adding a handler to the basicConfig
    # above but with the issue of stdout logging failing silently coupled with not having the experimental
    #  directory path prior to this point this workaround must be applied.
    logging.getLogger('').addHandler(log_file_handler)


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
            quit_message = '"{configuration.hostname}" is not a valid hostname.'.format(**locals())
            quit_message += ' Contact your local dev for instructions on setting a valid hostname.'
            logging.error(quit_message)
            quit()

        create_file_structure_for_experiment(configuration)
        set_up_log_file_with_base_handler(configuration.experiment_directory_path)

        try:
            perform_experiment(configuration)
        except KeyboardInterrupt:
            end_experiment(configuration, experiment_ended_message='Keyboard interrupt detected. Quitting...')

    # We might get a SubprocessError from check_call (which calls raspistill/s3),
    # but we also want to catch any other type of Exception
    except Exception as exception:
        logging.error("Unexpected exception occurred")
        logging.error(exception)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logging.error('\n'.join(traceback.format_tb(exc_traceback)))


if __name__ == '__main__':
    print('Please call "run_experiment" instead of "python experiment.py"')
