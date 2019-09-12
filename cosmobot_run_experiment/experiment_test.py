from datetime import datetime, timedelta
import pytest
from . import experiment as module


@pytest.fixture
def mock_hostname_is_correct(mocker):
    return mocker.patch.object(module, "hostname_is_correct")


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


MOCK_BASIC_PARAMETERS = [
    "--name",
    "automated_integration_test",
    "--interval",
    "0.1",  # Long enough to do an actual loop; not long enough to make the test feel slow
    "--duration",
    "0.1",  # Match duration to interval to force exactly one iteration
    "--skip-sync",
]


# A slightly unfortunate combination of integration and unit tests
class TestPerformExperiment:
    def test_perform_experiment_dry_run_with_basic_parameters(
        self, mock_capture, mock_free_space_for_one_image
    ):
        # Shortcut: use `get_experiment_configuration` to create the configuration (aka. make this an integration test)
        # Since `get_experiment_configuration` generates the start_date and end_date of the experiment,
        # the configuration must be used immediately
        mock_configuration = module.get_experiment_configuration(MOCK_BASIC_PARAMETERS)

        start_time = datetime.now()

        with pytest.raises(SystemExit):
            module.perform_experiment(mock_configuration)

        end_time = datetime.now()
        elapsed_time = end_time - start_time

        # Crude self-test that no major, slow side-effects are occurring:
        # For instance, if we are syncing to s3 we'd expect that to take a few seconds
        # and cause this to fail.
        max_test_time = timedelta(seconds=0.5)
        assert elapsed_time < max_test_time

        assert mock_capture.call_count == 1

    def test_ends_experiment_without_capture_if_no_free_space(
        self, mock_capture, mock_free_space_for_one_image
    ):
        mock_free_space_for_one_image.return_value = False
        mock_configuration = module.get_experiment_configuration(MOCK_BASIC_PARAMETERS)

        with pytest.raises(SystemExit):
            module.perform_experiment(mock_configuration)

        assert mock_capture.call_count == 0


class TestRunExperiment:
    def test_experiment_dry_run_with_basic_parameters(
        self,
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
