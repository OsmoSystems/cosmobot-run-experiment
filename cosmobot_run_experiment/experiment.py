import os
import sys
import time
import logging
import traceback

from cosmobot_run_experiment.file_structure import get_image_filename
from .camera import capture
from .file_structure import iso_datetime_for_filename, remove_experiment_directory
from .prepare import (
    create_file_structure_for_experiment,
    get_experiment_configuration,
    hostname_is_correct,
)
from .storage import free_space_for_one_image, how_many_images_with_free_space
from .sync_manager import end_syncing_process, sync_directory_in_separate_process
from .exposure import review_exposure_statistics
from .led_control import control_led

from datetime import datetime, timedelta


# Basic logging configuration - sets the base log level to INFO and provides a
# log format (time, log level, log message) for all messages to be written to stdout (console)
# or to a log file. This is set outside of a function as the execution path through testing
# shows that setting the values inside a function causes some silent failure with stdout to a console.
logging_format = "%(asctime)s [%(levelname)s]--- %(message)s"
logging.basicConfig(
    level=logging.INFO, format=logging_format, handlers=[logging.StreamHandler()]
)


def _end_experiment_if_not_enough_space(configuration):
    if not free_space_for_one_image():
        end_experiment(
            configuration,
            experiment_ended_message="Insufficient space to save the image. Quitting...",
            has_errored=True,
        )


def _get_variant_image_filepath(variant, experiment_directory_path):
    capture_timestamp = datetime.now()

    image_filename = get_image_filename(capture_timestamp, variant)
    return os.path.join(experiment_directory_path, image_filename)


def perform_experiment(configuration):
    """Perform experiment using settings passed in through the configuration.
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
    """
    duration = configuration.duration

    # print out warning that no duration has been set and inform how many
    # estimated images can be stored
    if duration is None:
        how_many_images_can_be_captured = how_many_images_with_free_space()
        logging.info("No experimental duration provided.")
        logging.info(
            "Estimated number of images that can be captured with free space: "
            f"{how_many_images_can_be_captured}"
        )
    # Start capturing immediately
    first_capture_time = datetime.now()
    next_capture_time = first_capture_time

    # Continue capturing for set duration or indefinitely
    last_capture_time = (
        None if duration is None else first_capture_time + timedelta(seconds=duration)
    )

    while last_capture_time is None or datetime.now() < last_capture_time:
        if datetime.now() < next_capture_time:
            time.sleep(0.1)  # No need to totally peg the CPU
            continue

        # next_capture_time is agnostic to the time needed for capture and writing of image
        next_capture_time = next_capture_time + timedelta(
            seconds=configuration.interval
        )

        # iterate through each capture variant and capture an image with it's settings
        for variant in configuration.variants:
            _end_experiment_if_not_enough_space(configuration)

            experiment_directory_path = configuration.experiment_directory_path
            image_filepath = _get_variant_image_filepath(
                variant, experiment_directory_path
            )

            capture(
                image_filepath,
                exposure_time=variant.exposure_time,
                iso=variant.iso,
                warm_up_time=variant.camera_warm_up,
                additional_capture_params=variant.additional_capture_params,
            )

            # Doubly ensure the LED is turned off after capture (in case something goes wrong in raspistill land)
            control_led(led_on=False)

            # If a sync is currently occuring, this is a no-op.
            if not configuration.skip_sync:
                sync_directory_in_separate_process(experiment_directory_path)

    end_experiment(
        configuration,
        experiment_ended_message="Experiment completed successfully!",
        has_errored=False,
    )


def _perform_final_sync(experiment_directory_path, erase_synced_files):
    """ If a file(s) is written after a sync process begins it does not get added to the list to sync.
        This is fine during an experiment, but at the end of the experiment, we want to make sure to sync all the
        remaining images. To that end, we end any existing sync process and start a new one
    """
    logging.info("Beginning final sync to s3 due to end of experiment...")
    end_syncing_process()
    sync_directory_in_separate_process(
        experiment_directory_path,
        wait_for_finish=True,
        exclude_log_files=False,
        erase_synced_files=erase_synced_files,
    )
    logging.info("Final sync to s3 completed!")

    # s3 mv does not remove a directory so we have to do it here after mv is complete
    if erase_synced_files:
        remove_experiment_directory(experiment_directory_path)


def end_experiment(experiment_configuration, experiment_ended_message, has_errored):
    """ Complete an experiment by ensuring all remaining images finish syncing, then exit

    Args:
        experiment_configuration: experiment configuration namedtuple
        experiment_ended_message: message to log about why experiment ended
        has_errored: whether the experiment is being ended due to an error. If True, this will exit the process with
        exit status of 1.

    Returns:
        None (exits with 1 if has_errored, otherwise 0)
    """
    control_led(led_on=False)
    logging.info(experiment_ended_message)

    if not experiment_configuration.skip_sync:
        _perform_final_sync(
            experiment_configuration.experiment_directory_path,
            experiment_configuration.erase_synced_files,
        )

    if experiment_configuration.review_exposure:
        review_exposure_statistics(experiment_configuration.experiment_directory_path)

    sys.exit(1 if has_errored else 0)


def set_up_log_file_with_base_handler(experiment_directory, start_date):
    iso_ish_datetime = iso_datetime_for_filename(start_date)
    log_filepath = os.path.join(
        experiment_directory, f"{iso_ish_datetime}_experiment.log"
    )
    log_file_handler = logging.FileHandler(log_filepath)
    formatter = logging.Formatter(logging_format)
    log_file_handler.setFormatter(formatter)

    # Retrieve the root logger object that the module level logging.[loglevel] object uses
    # and adds the additional "log to file" handler.  This is similar to adding a handler to the basicConfig
    # above but with the issue of stdout logging failing silently coupled with not having the experimental
    #  directory path prior to this point this workaround must be applied.
    logging.getLogger("").addHandler(log_file_handler)


def run_experiment(cli_args=None):
    """ Top-level function to run an experiment.
    Collects command-line arguments, captures images, and syncs them to s3.
    Also checks that the system has the correct hostname configured and handles graceful closure upon KeyboardInterrupt.

    On error, it will log the error and exit with a non-zero status code.

    Args:
        cli_args: Optional: list of command-line argument strings like sys.argv. If not provided, sys.argv will be used
    Returns:
        None
    """
    try:
        if cli_args is None:
            # First argument is the name of the command itself, not an "argument" we want to parse
            cli_args = sys.argv[1:]
        configuration = get_experiment_configuration(cli_args)

        if not hostname_is_correct(configuration.hostname):
            quit_message = (
                f'"{configuration.hostname}" is not a valid hostname.'
                " Contact your local dev for instructions on setting a valid hostname."
            )
            logging.error(quit_message)
            sys.exit(1)

        create_file_structure_for_experiment(configuration)
        set_up_log_file_with_base_handler(
            configuration.experiment_directory_path, configuration.start_date
        )

        try:
            perform_experiment(configuration)
        except KeyboardInterrupt:
            end_experiment(
                configuration,
                experiment_ended_message="Keyboard interrupt detected. Quitting...",
                has_errored=True,
            )

    # We might get a SubprocessError from check_call (which calls raspistill/s3),
    # but we also want to catch any other type of Exception
    except Exception as exception:
        logging.error("Unexpected exception occurred")
        logging.error(exception)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logging.error("\n".join(traceback.format_tb(exc_traceback)))
        sys.exit(1)


if __name__ == "__main__":
    print('Please call "run_experiment" instead of "python experiment.py"')
