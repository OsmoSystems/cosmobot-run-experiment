import pytest
import multiprocessing
import psutil
from . import sync_manager as module
from . import s3


@pytest.fixture
def mock_sync_process(mocker):
    return mocker.patch.object(module, '_SYNC_PROCESS')


@pytest.fixture
def mock_psutil_process(mocker):
    mock_psutil_process = mocker.patch.object(psutil, 'Process')
    mock_psutil_process.return_value.pid = 10000
    mock_psutil_process.return_value.children = lambda recursive: []
    mock_psutil_process.return_value.kill.return_value = True
    return mock_psutil_process


@pytest.fixture
def mock_multiprocess_process(mocker):
    mock_multiprocess_process = mocker.patch.object(multiprocessing, 'Process')
    mock_multiprocess_process.return_value.start = lambda: True
    mock_multiprocess_process.return_value.pid = 10000
    return mock_multiprocess_process


class TestIsSyncProcessRunning:
    def test_process_doesnt_exist__return_falsey(self):
        module._SYNC_PROCESS = None
        assert not module._is_sync_process_running()

    def test_process_exists_but_terminated__return_falsey(self, mock_sync_process):
        mock_sync_process.is_alive.return_value = False
        assert not module._is_sync_process_running()

    def test_process_exists_and_is_running__return_truthy(self, mock_sync_process):
        mock_sync_process.is_alive.return_value = True
        assert module._is_sync_process_running()

    def test_process_exists_and_is_running_and_excludes_logs(self, mock_multiprocess_process):
        module.sync_directory_in_separate_process('/tmp', wait_for_finish=False, exclude_log_files=True)
        expected_additional_sync_params = '--exclude *.log*'
        mock_multiprocess_process.assert_called_with(
            target=s3.sync_to_s3,
            args=('/tmp', expected_additional_sync_params,)
        )


class TestEndSyncingProcess:
    def test_process_not_running__dont_attempt_to_terminate_it(self, mocker, mock_sync_process):
        mocker.patch.object(module, '_is_sync_process_running').return_value = False
        module.end_syncing_process()
        mock_sync_process.terminate.assert_not_called()

    def test_process_running__kill_it(
        self,
        mocker,
        mock_sync_process,
        mock_multiprocess_process,
        mock_psutil_process
    ):
        mocker.patch.object(module, '_is_sync_process_running').return_value = True
        module.end_syncing_process()
        assert mock_psutil_process.return_value.kill.call_count == 1
