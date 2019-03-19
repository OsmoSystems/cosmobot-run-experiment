import os


def get_base_output_path():
    # Store output in pi user's home directory even if this command is run as root
    return '/home/pi/camera-sensor-output/'


def iso_datetime_for_filename(datetime):
    ''' Returns datetime as a ISO-ish format string that can be used in filenames (which can't inclue ":")
        datetime(2018, 1, 1, 12, 1, 1) --> '2018-01-01--12-01-01'
    '''
    return datetime.strftime('%Y-%m-%d--%H-%M-%S')


def get_files_with_extension(directory, extension):
    ''' Get all file paths in the given directory with the given extension, sorted alphanumerically

        NOTE: Duplicated from process_experiment

    Args:
        directory: The full path to the directory of files
        extension: The full extension (including '.') of files to filter to, e.g. '.jpeg'

    Returns:
        A sorted list of full file paths
    '''
    file_paths = [
        os.path.join(directory, filename)
        for filename in os.listdir(directory)
        if os.path.splitext(filename)[1] == extension  # splitext() splits into a tuple of (root, extension)
    ]

    return sorted(file_paths)


def remove_experiment_directory(experiment_directory):
    ''' Remove experiment directory

        Note: os.rmdir only removes an empty directory
    Args:
        experiment_directory: directory to remove

    Returns:
        None
    '''

    directory = os.path.join(get_base_output_path(), experiment_directory)
    os.rmdir(directory)
