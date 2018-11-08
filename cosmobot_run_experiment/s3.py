import os
import logging
from subprocess import check_call


def sync_to_s3(local_sync_dir, additional_sync_params=''):
    ''' Syncs raw images from a local directory to the s3://camera-sensor-experiments bucket

    Args:
        local_sync_dir: The full path of the directory to sync locally

    Returns:
       None
    '''

    # Using CLI vs boto: https://github.com/boto/boto3/issues/358
    # It looks like sync is not a supported function of the python boto library
    # Work around is to use cli sync for now (requires aws cli to be installed)
    logging.info(f'Performing sync of experiments directory: {local_sync_dir}')
    experiment_dir_name = os.path.basename(os.path.normpath(local_sync_dir))

    # This argument pattern issues a uni-directional sync to S3 bucket
    # https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html
    s3_sync_dir = f's3://camera-sensor-experiments/{experiment_dir_name}'
    command = f'aws s3 sync {local_sync_dir} {s3_sync_dir} {additional_sync_params}'
    logging.info(f'{command}')
    check_call(command, shell=True)
