import os
from datetime import datetime, timedelta

from .camera import capture
from .file_structure import iso_datetime_for_filename
from .prepare import hostname_is_valid, get_experiment_configuration, create_file_structure_for_experiment
from .storage import how_many_images_with_free_space, free_space_for_one_image
from .sync_manager import sync_directory_in_separate_process, end_syncing_process


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
        print('No experimental duration provided.')
        print(f'Estimated number of images that can be captured with free space: {how_many_images_can_be_captured}')

    # Initial value of start_date results in immediate capture on first iteration in while loop
    next_capture_time = configuration.start_date

    while configuration.duration is None or datetime.now() < configuration.end_date:
        if datetime.now() < next_capture_time:
            continue

        # next_capture_time is agnostic to the time needed for capture and writing of image
        next_capture_time = next_capture_time + timedelta(seconds=configuration.interval)

        # iterate through each capture variant and capture an image with it's settings
        for variant in configuration.variants:

            if not free_space_for_one_image():
                end_experiment(configuration, quit_message='Insufficient space to save the image. Quitting.')

            iso_ish_datetime = iso_datetime_for_filename(datetime.now())
            capture_params_for_filename = variant.capture_params.replace('-', '').replace(' ', '_')
            image_filename = f'{iso_ish_datetime}{capture_params_for_filename}.jpeg'
            image_filepath = os.path.join(configuration.experiment_directory_path, image_filename)

            capture(image_filepath, additional_capture_params=variant.capture_params)

            # If a sync is currently occuring, this is a no-op.
            sync_directory_in_separate_process(configuration.experiment_directory_path)

    end_experiment(configuration, quit_message='Experiment completed successfully!')


def end_experiment(experiment_configuration, quit_message):
    ''' Complete an experiment by ensuring all remaining images finish syncing '''
    # If a file(s) is written after a sync process begins it does not get added to the list to sync.
    # This is fine during an experiment, but at the end of the experiment, we want to make sure to sync all the
    # remaining images. To that end, we end any existing sync process and start a new one
    end_syncing_process()
    sync_directory_in_separate_process(experiment_configuration.experiment_directory_path, wait_for_finish=True)
    quit(quit_message)


def run_experiment():
    configuration = get_experiment_configuration()

    if not hostname_is_valid(configuration.hostname):
        quit_message = f'"{configuration.hostname}" is not a valid hostname.'
        quit_message += ' Contact your local dev for instructions on setting a valid hostname.'
        quit(quit_message)

    create_file_structure_for_experiment(configuration)

    try:
        perform_experiment(configuration)
    except KeyboardInterrupt:
        print('Keyboard interrupt detected, attempting final sync')
        end_experiment(configuration, quit_message='Final sync after keyboard interrupt completed.')


if __name__ == '__main__':
    print('Please call "run_experiment" instead of "python experiment.py"')
