from datetime import datetime, timedelta
import logging
import pytest
from . import experiment as module


class TestRunExperiment:
    def test_experiment_dry_run_with_basic_parameters(self, mocker):
        # This isn't a super-hard-core full-stack integration test;
        # mock out inconvenient side-effects
        mock_hostname_is_correct = mocker.patch.object(module, 'hostname_is_correct')
        mock_hostname_is_correct.return_value = True
        mock_create_file_structure = mocker.patch.object(module, 'create_file_structure_for_experiment')
        mock_capture = mocker.patch.object(module, 'capture')

        mocker.patch.object(logging, 'info')
        mocker.patch.object(logging, 'error')
        mocker.patch.object(logging, 'getLogger')
        mocker.patch.object(logging, 'FileHandler')

        # Long enough to do an actual loop; not long enough to make the test feel slow
        duration = 0.1

        start_time = datetime.now()
        with pytest.raises(SystemExit, message='Experiment completed successfully!'):
            module.run_experiment([
                '--name', 'automated_integration_test',
                '--interval', str(duration),
                '--duration', str(duration),
                '--skip-sync'
            ])
        end_time = datetime.now()
        elapsed_time = end_time - start_time

        mock_capture.assert_called_once()
        mock_create_file_structure.assert_called_once()
        mock_hostname_is_correct.assert_called_once()

        # Crude self-test that no major, slow side-effects are occurring:
        # For instance, if we are syncing to s3 we'd expect that to take a few seconds
        # and cause this to fail.
        max_test_time = timedelta(seconds=0.5)
        assert elapsed_time < max_test_time
