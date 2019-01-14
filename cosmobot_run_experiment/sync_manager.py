import multiprocessing
import psutil
from .s3 import sync_to_s3


_SYNC_PROCESS = None


def _is_sync_process_running():
    return _SYNC_PROCESS and _SYNC_PROCESS.is_alive()


def end_syncing_process():
    '''Stops the syncing process. Intended to be used if experimental image capture has finished and a final
       sync should be initiated.

       Note: we need to make sure to kill all child & descendant processes
       (_SYNC_PROCESS.terminate() would only kill the top level
       https://docs.python.org/3.5/library/multiprocessing.html#multiprocessing.Process.terminate)
     Args:
        None
     Returns:
        None
    '''
    global _SYNC_PROCESS

    if _is_sync_process_running():
        sync_process_parent = psutil.Process(_SYNC_PROCESS.pid)
        for child in sync_process_parent.children(recursive=True):
            child.kill()

        sync_process_parent.kill()

        _SYNC_PROCESS = None


def sync_directory_in_separate_process(
    directory, wait_for_finish=False,
    exclude_log_files=True,
    erase_synced_files=False
):
    ''' Instantiates a separate process for syncing a directory to s3.  Stores a reference to the process to check
        later for subsequent syncs.
     Args:
        directory: directory to sync
        wait_for_finish (optional): If True, wait for new process to complete before returning from the function.
     Returns:
        None.
    '''
    global _SYNC_PROCESS
    if _is_sync_process_running():
        return

    additional_sync_params = '--exclude *.log*' if exclude_log_files else ''

    _SYNC_PROCESS = multiprocessing.Process(
        target=sync_to_s3,
        args=(directory, additional_sync_params, erase_synced_files,)
    )
    _SYNC_PROCESS.start()

    if wait_for_finish:
        # .join() means "wait for a thread to complete"
        _SYNC_PROCESS.join()
