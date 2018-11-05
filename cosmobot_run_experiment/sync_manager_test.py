import pytest
from . import sync_manager as module


@pytest.fixture
def mock_sync_process(mocker):
    return mocker.patch.object(module, '_SYNC_PROCESS')


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


class TestEndSyncingProcess:
    def test_process_not_running__dont_blow_up(self, mocker, mock_sync_process):
        mocker.patch.object(module, '_is_sync_process_running').return_value = False
        module.end_syncing_process()
        mock_sync_process.terminate.assert_not_called()

    def test_process_running__kill_it(self, mocker, mock_sync_process):
        mocker.patch.object(module, '_is_sync_process_running').return_value = True
        module.end_syncing_process()
        mock_sync_process.terminate.assert_called_once()