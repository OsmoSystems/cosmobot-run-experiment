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


# COPY-PASTA from cosmobot-process-experiment
class TestListExperiments:
    def test_returns_cleaned_sorted_directories(self, mocker):
        mocker.patch.object(
            module, "list_camera_sensor_experiments_s3_bucket_contents"
        ).return_value = [
            "2018-01-01--12-01-01_directory_1/",
            "2018-01-01--12-02-01_directory_2/",
        ]
        assert module.list_experiments() == [
            "2018-01-01--12-02-01_directory_2",
            "2018-01-01--12-01-01_directory_1",
        ]


UNORDERED_UNFILTERED_LIST_FOR_TESTS = [
    "20180902103709_temperature",
    "20180902103940_temperature",
    "2018-11-08--11-25-27-Pi4E82-test",
    "2018-11-08--11-26-00-Pi4E82-test",
    "should_be_filtered.jpng",
]


# COPY-PASTA from cosmobot-process-experiment
class TestFilterAndSortExperimentList:
    def test_returns_filtered_list_for_new_isodate_format(self):
        actual_filtered_list = module._experiment_list_by_isodate_format_date_desc(
            UNORDERED_UNFILTERED_LIST_FOR_TESTS
        )
        expected_filtered_list = [
            "2018-11-08--11-26-00-Pi4E82-test",
            "2018-11-08--11-25-27-Pi4E82-test",
        ]
        assert actual_filtered_list == expected_filtered_list
