import datetime
import os


_FILENAME_DATETIME_FORMAT = "%Y-%m-%d--%H-%M-%S"
FILENAME_TIMESTAMP_LENGTH = len("2018-01-01--12-01-01")


def get_base_output_path():
    # Store output in pi user's home directory even if this command is run as root
    return "/home/pi/camera-sensor-output/"


def iso_datetime_for_filename(datetime_):
    """ Returns datetime as a ISO-ish format string that can be used in filenames (which can't inclue ":")
        datetime(2018, 1, 1, 12, 1, 1) --> '2018-01-01--12-01-01'
    """
    return datetime_.strftime("%Y-%m-%d--%H-%M-%S")


def _process_param_for_filename(param):
    """ prep param for a filename by removing common problem characters
    Args:
        param: parameter value - expected to be a string or number
    Returns:
        string that is safer to use as a filename
    """
    handled_types = (str, int, float)
    if not isinstance(param, handled_types):
        raise TypeError(
            f"I'm not sure I know how to handle this param of type {type(param)}: {param}"
        )
    return str(param).replace("-", "").replace(" ", "_")


def get_image_filename(current_datetime, variant):
    """
    Args:
        current_datetime: datetime.datetime instance for when the image is taken
        variant: ExperimentVariant instance for this image

    Returns:
        string - image filename including extension
    """
    iso_ish_datetime = iso_datetime_for_filename(current_datetime)
    variant_params_for_filename = "_".join(
        "{}_{}".format(
            _process_param_for_filename(key), _process_param_for_filename(value)
        )
        for key, value in variant._asdict().items()
    )
    image_filename = f"{iso_ish_datetime}_{variant_params_for_filename}_.jpeg"
    return image_filename


def get_files_with_extension(directory, extension):
    """ Get all file paths in the given directory with the given extension, sorted alphanumerically

        NOTE: Duplicated from process_experiment

    Args:
        directory: The full path to the directory of files
        extension: The full extension (including '.') of files to filter to, e.g. '.jpeg'

    Returns:
        A sorted list of full file paths
    """
    file_paths = [
        os.path.join(directory, filename)
        for filename in os.listdir(directory)
        # splitext() splits into a tuple of (root, extension)
        if os.path.splitext(filename)[1] == extension
    ]

    return sorted(file_paths)


def remove_experiment_directory(experiment_directory):
    """ Remove experiment directory

        Note: os.rmdir only removes an empty directory
    Args:
        experiment_directory: directory to remove

    Returns:
        None
    """

    directory = os.path.join(get_base_output_path(), experiment_directory)
    os.rmdir(directory)


# COPY-PASTA from cosmobot-process-experiment
def datetime_from_filename(filename: str) -> datetime.datetime:
    """ Recover a datetime that has been encoded into a filename, also returning the remainder of the filename

    Arguments:
        filename: filename to process. Should start with an ISO-ish datetime
            as produced by iso_datetime_for_filename()
    Returns:
        a datetime.datetime object matching the one that was encoded in the filename
    """

    return datetime.datetime.strptime(
        filename[:FILENAME_TIMESTAMP_LENGTH], _FILENAME_DATETIME_FORMAT
    )


# COPY-PASTA from cosmobot-process-experiment
def filename_has_correct_datetime_format(filename):
    """ Is an ISO formatted date a substring at the start of filename

    Arguments:
        filename: filename to validate
    Returns:
        a true/false value that is used to validate file format is correct
    """

    try:
        datetime_from_filename(filename)
        return True
    except ValueError:
        return False
