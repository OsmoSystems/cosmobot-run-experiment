import pytest

from . import s3 as module


@pytest.fixture
def mock_check_call(mocker):
    mock_check_call = mocker.patch.object(module, "check_call")
    mock_check_call.return_value = None

    return mock_check_call


@pytest.fixture
def mock_path_basename(mocker):
    mock_path_basename = mocker.patch("os.path.basename")
    mock_path_basename.return_value = "experiment_name"
    return mock_path_basename


class TestSyncToS3:
    def test_syncs_to_subdirectory_in_s3_bucket(
        self, mocker, mock_check_call, mock_path_basename
    ):
        module.sync_to_s3(local_sync_dir="/output_dir/experiment_name")

        expected_command = (
            "/home/pi/.local/bin/aws s3 sync /output_dir/experiment_name "
            "s3://camera-sensor-experiments/experiment_name "
        )
        mock_check_call.assert_called_with(expected_command, shell=True)

    def test_syncs_to_subdirectory_in_s3_bucket_with_additional_sync_params(
        self, mocker, mock_check_call, mock_path_basename
    ):
        module.sync_to_s3(
            local_sync_dir="/output_dir/experiment_name",
            additional_sync_params="--exclude *.log*",
        )

        expected_command = (
            "/home/pi/.local/bin/aws s3 sync /output_dir/experiment_name "
            "s3://camera-sensor-experiments/experiment_name --exclude *.log*"
        )
        mock_check_call.assert_called_with(expected_command, shell=True)

    @pytest.mark.parametrize(
        "test_name, erase_synced_files, expected_command",
        [
            (
                "mv",
                True,
                "/home/pi/.local/bin/aws s3 mv --recursive /output_dir/experiment_name "
                "s3://camera-sensor-experiments/experiment_name ",
            ),
            (
                "sync",
                False,
                "/home/pi/.local/bin/aws s3 sync /output_dir/experiment_name "
                "s3://camera-sensor-experiments/experiment_name ",
            ),
        ],
    )
    def test_s3_subcommand(
        self,
        test_name,
        erase_synced_files,
        expected_command,
        mocker,
        mock_check_call,
        mock_path_basename,
    ):
        module.sync_to_s3(
            local_sync_dir="/output_dir/experiment_name",
            erase_synced_files=erase_synced_files,
        )
        mock_check_call.assert_called_with(expected_command, shell=True)
