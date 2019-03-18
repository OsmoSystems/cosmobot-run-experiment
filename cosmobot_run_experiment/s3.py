import os
import logging
from subprocess import check_call


def sync_to_s3(local_sync_dir, additional_sync_params='', erase_synced_files=False):
    ''' Syncs raw images from a local directory to the s3://camera-sensor-experiments bucket

    Args:
        local_sync_dir: The full path of the directory to sync locally
        additional_sync_params: Additional parameters to send to aws s3 cli command
        erase_synced_files: If True, use aws s3 mv command to erase files after sync

    Returns:
       None
    '''

    # Using CLI vs boto: https://github.com/boto/boto3/issues/358
    # It looks like sync is not a supported function of the python boto library
    # Work around is to use cli sync for now (requires aws cli to be installed)
    logging.info('Performing sync of experiments directory: {local_sync_dir}'.format(**locals()))
    experiment_dir_name = os.path.basename(os.path.normpath(local_sync_dir))
    s3_subcommand = 'mv --recursive' if erase_synced_files else 'sync'

    # This argument pattern issues a uni-directional sync to S3 bucket
    # https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html or
    # https://docs.aws.amazon.com/cli/latest/reference/s3/mv.html
    s3_sync_dir = 's3://camera-sensor-experiments/{experiment_dir_name}'.format(**locals())
    # aws-cli is installed and set up as the pi user, but this command has to be run as
    # sudo for now, so we have to manually specify some files.
    # followup: https://app.asana.com/0/819671808102776/1106347012732358/f
    command = 'aws s3 {s3_subcommand} {local_sync_dir} {s3_sync_dir} {additional_sync_params}'.format(**locals())
    logging.info(command)
    check_call(command, shell=True)
