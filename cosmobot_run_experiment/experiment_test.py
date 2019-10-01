from datetime import datetime, timedelta
from unittest.mock import sentinel

from freezegun import freeze_time
import pytest

from .prepare import ExperimentConfiguration, ExperimentVariant
from . import experiment as module


@pytest.fixture
def mock_hostname_is_correct(mocker):
    return mocker.patch.object(module, "hostname_is_correct")


@pytest.fixture
def mock_get_experiment_configuration(mocker):
    return mocker.patch.object(module, "get_experiment_configuration")


@pytest.fixture
def mock_create_file_structure_for_experiment(mocker):
    return mocker.patch.object(module, "create_file_structure_for_experiment")


@pytest.fixture
def mock_perform_experiment(mocker):
    return mocker.patch.object(module, "perform_experiment")


@pytest.fixture
def mock_capture(mocker):
    return mocker.patch.object(module, "capture")


@pytest.fixture
def mock_set_up_log_file_with_base_handler(mocker):
    return mocker.patch.object(module, "set_up_log_file_with_base_handler")


@pytest.fixture
def mock_free_space_for_one_image(mocker):
    mock_free_space_for_one_image = mocker.patch.object(
        module, "free_space_for_one_image"
    )
    mock_free_space_for_one_image.return_value = True
    return mock_free_space_for_one_image


MOCK_EXPERIMENT_CONFIGURATION = {
    "name": "automated_integration_test",
    "duration": 0.1,
    "interval": 0.1,
    "variants": [
        ExperimentVariant(
            additional_capture_params="", iso=500, exposure_time=0.123, camera_warm_up=4
        )
    ],
    "group_results": False,
    "experiment_directory_path": "/mock/path/to",
    "start_date": sentinel.start_date,
    "command": sentinel.command,
    "git_hash": sentinel.git_hash,
    "ip_addresses": sentinel.ip_addresses,
    "hostname": sentinel.hostname,
    "mac": sentinel.mac,
    "skip_sync": True,
    "erase_synced_files": False,
    "review_exposure": False,
}


def _mock_experiment_configuration_with(**kwargs):
    return ExperimentConfiguration(**{**MOCK_EXPERIMENT_CONFIGURATION, **kwargs})


class TestPerformExperiment:
    def test_dry_run_duration_roughly_correct(
        self, mock_capture, mock_free_space_for_one_image
    ):
        start_time = datetime.now()
        mock_configuration = _mock_experiment_configuration_with(duration=0.2)

        with pytest.raises(SystemExit):
            module.perform_experiment(mock_configuration)

        end_time = datetime.now()
        elapsed_time = end_time - start_time

        # Crude self-test that no major, slow side-effects are occurring:
        # For instance, if we are syncing to s3 we'd expect that to take a few seconds
        # and cause this to fail.
        max_test_time = timedelta(seconds=0.3)
        assert elapsed_time < max_test_time

    @freeze_time("2019-01-01 12:00:01")
    def test_capture_called_with_correct_params(
        self, mock_capture, mock_free_space_for_one_image
    ):
        # With time frozen, force the experiment to end
        mock_capture.side_effect = SystemExit()

        mock_configuration = _mock_experiment_configuration_with()

        with pytest.raises(SystemExit):
            module.perform_experiment(mock_configuration)

        expected_filepath = "/mock/path/to/2019-01-01--12-00-01_additional_capture_params__exposure_time_0.123_iso_500_camera_warm_up_4_.jpeg"  # noqa: E501 line too long
        mock_capture.assert_called_with(
            expected_filepath,
            exposure_time=0.123,
            iso=500,
            warm_up_time=4,
            additional_capture_params="",
        )

    def test_image_count_roughly_correct(
        self, mock_capture, mock_free_space_for_one_image
    ):
        mock_configuration = _mock_experiment_configuration_with(
            duration=0.5, interval=0.2
        )

        with pytest.raises(SystemExit):
            module.perform_experiment(mock_configuration)

        assert mock_capture.call_count == 3

    def test_ends_experiment_without_capture_if_no_free_space(
        self, mock_capture, mock_free_space_for_one_image
    ):
        mock_free_space_for_one_image.return_value = False
        mock_configuration = _mock_experiment_configuration_with()

        with pytest.raises(SystemExit):
            module.perform_experiment(mock_configuration)

        assert mock_capture.call_count == 0


MOCK_BASIC_PARAMETERS = [
    "--name",
    "automated_integration_test",
    "--interval",
    "0.1",  # Long enough to do an actual loop; not long enough to make the test feel slow
    "--duration",
    "0.1",  # Match duration to interval to force exactly one iteration
    "--skip-sync",
]


class TestRunExperiment:
    def test_experiment_dry_run_with_basic_parameters(
        self,
        mock_get_experiment_configuration,
        mock_hostname_is_correct,
        mock_create_file_structure_for_experiment,
        mock_set_up_log_file_with_base_handler,
        mock_perform_experiment,
    ):
        mock_hostname_is_correct.return_value = True

        module.run_experiment(MOCK_BASIC_PARAMETERS)

        assert mock_create_file_structure_for_experiment.call_count == 1
        assert mock_hostname_is_correct.call_count == 1
        assert mock_set_up_log_file_with_base_handler.call_count == 1
        assert mock_perform_experiment.call_count == 1

    def test_exits_early_if_hostname_is_incorrect(
        self,
        mock_get_experiment_configuration,
        mock_hostname_is_correct,
        mock_create_file_structure_for_experiment,
        mock_set_up_log_file_with_base_handler,
        mock_perform_experiment,
    ):
        mock_hostname_is_correct.return_value = False

        with pytest.raises(SystemExit) as exception_info:
            module.run_experiment(MOCK_BASIC_PARAMETERS)

        assert exception_info.value.code == 1
        assert mock_perform_experiment.call_count == 0
