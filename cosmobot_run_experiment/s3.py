import os
import logging
from subprocess import check_call
from typing import List

import boto

from . import file_structure


CAMERA_SENSOR_EXPERIMENTS_BUCKET_NAME = "camera-sensor-experiments"


def sync_to_s3(local_sync_dir, additional_sync_params="", erase_synced_files=False):
    """ Syncs raw images from a local directory to the s3://camera-sensor-experiments bucket

    Args:
        local_sync_dir: The full path of the directory to sync locally
        additional_sync_params: Additional parameters to send to aws s3 cli command
        erase_synced_files: If True, use aws s3 mv command to erase files after sync

    Returns:
       None
    """

    # Using CLI vs boto: https://github.com/boto/boto3/issues/358
    # It looks like sync is not a supported function of the python boto library
    # Work around is to use cli sync for now (requires aws cli to be installed)
    logging.info(f"Performing sync of experiments directory: {local_sync_dir}")
    experiment_dir_name = os.path.basename(os.path.normpath(local_sync_dir))
    s3_subcommand = "mv --recursive" if erase_synced_files else "sync"

    # This argument pattern issues a uni-directional sync to S3 bucket
    # https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html or
    # https://docs.aws.amazon.com/cli/latest/reference/s3/mv.html
    s3_sync_dir = f"s3://camera-sensor-experiments/{experiment_dir_name}"

    command = (
        f"/home/pi/.local/bin/aws s3 {s3_subcommand} {local_sync_dir} "
        f"{s3_sync_dir} {additional_sync_params}"
    )
    logging.info(command)
    check_call(command, shell=True)


# COPY-PASTA: from cosmobot-process-experiment
def list_camera_sensor_experiments_s3_bucket_contents(
    directory_name: str = ""
) -> List[str]:
    """ Get a list of all of the files in a logical directory off s3, within the camera sensor experiments bucket.

    Arguments:
        directory_name: prefix within our experiments bucket on s3, inclusive of trailing slash if you'd like the list
            of files within a "directory". Default is '' to get the top-level index of the bucket.

    Returns:
        list of key names under the prefix provided.
    """
    try:
        s3 = boto.connect_s3()
    except boto.exception.NoAuthHandlerFound:  # type: ignore
        print(
            "You must have aws credentials already saved, e.g. via `aws configure`. \n"
        )
        raise

    bucket = s3.get_bucket(CAMERA_SENSOR_EXPERIMENTS_BUCKET_NAME)
    keys = bucket.list(directory_name, delimiter="/")

    return list([key.name for key in keys])


# COPY-PASTA from cosmobot-process-experiment
def _experiment_list_by_isodate_format_date_desc(experiment_names):
    # Filter only filenames that contain the correct iso date format and reverse, sorting most recent first
    filtered_list = [
        experiment_name
        for experiment_name in experiment_names
        if file_structure.filename_has_correct_datetime_format(experiment_name)
    ]
    return sorted(filtered_list, reverse=True)


# COPY-PASTA from cosmobot-process-experiment
def list_experiments():
    """ Lists all experiment directories in the "camera-sensor-experiments" bucket

        Returns: a list of experiment names that is filtered and ordered (by isodate formats YYYY-MM-DD & YYYYMMDD)
        The list will be a concatenated set of lists, with the items starting with a list of YYYY-MM-DD formated names
        that are ordered by descending date followed by the same ordering but with a list of YYYYMMDD formatted names.
    """
    experiment_directories = list_camera_sensor_experiments_s3_bucket_contents("")

    experiment_names = [directory.rstrip("/") for directory in experiment_directories]

    return _experiment_list_by_isodate_format_date_desc(experiment_names)
