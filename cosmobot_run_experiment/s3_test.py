import pytest

from . import s3 as module


@pytest.fixture
def mock_check_call(mocker):
    mock_check_call = mocker.patch.object(module, 'check_call')
    mock_check_call.return_value = None

    return mock_check_call


class TestSyncToS3:
    def test_syncs_to_subdirectory_in_s3_bucket(self, mocker, mock_check_call):
        mock_path_basename = mocker.patch('os.path.basename')
        mock_path_basename.return_value = 'experiment_name'

        module.sync_to_s3(local_sync_dir='/output_dir/experiment_name')

        expected_command = f'aws s3 sync /output_dir/experiment_name s3://camera-sensor-experiments/experiment_name'
        mock_check_call.assert_called_with(expected_command, shell=True)