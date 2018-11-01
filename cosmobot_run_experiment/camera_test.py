import pytest
from . import camera as module


class TestCapture:
    def test_makes_expected_call_with_minimal_params(self, mocker):
        mock_check_call = mocker.patch.object(module, 'check_call')

        filename = 'output_file.jpeg'
        expected_command = 'raspistill --raw -o "output_file.jpeg"  -q 100 -awb off -awbg 1.307,1.615'

        module.capture(filename)

        expected_call = mocker.call(expected_command, shell=True)

        mock_check_call.assert_has_calls([expected_call])

    def test_makes_call_with_additional_capture_params_padded_with_spaces(self, mocker):
        mock_check_call = mocker.patch.object(module, 'check_call')
        additional_capture_params = 'additional!!'

        module.capture('doesnt matter', additional_capture_params)

        # Call args looks like [call(command, shell=True)] where call is a tuple
        actual_call_command = mock_check_call.call_args[0][0]

        padded_additional_capture_params = f' {additional_capture_params} '
        assert padded_additional_capture_params in actual_call_command

    def test_blows_up_if_check_call_fails(self, mocker):
        # This is a common occurence at the start of an (attempted) experiment
        mocker.patch.object(module, 'check_call').side_effect = Exception(
            "omg something else is using the camera and I don't know what to do :'(''"
        )

        with pytest.raises(Exception):
            module.capture('', '')


class TestSimulateCaptureWithCopy:
    def test_calls_something_other_than_raspistill(self, mocker):
        mock_check_call = mocker.patch.object(module, 'check_call')

        module.simulate_capture_with_copy('doesnt matter')

        # Call args looks like [call(command, shell=True)] where call is a tuple
        actual_call_command = mock_check_call.call_args[0][0]

        assert 'raspistill' not in actual_call_command

    def test_accepts_additional_capture_params(self, mocker):
        mock_check_call = mocker.patch.object(module, 'check_call')
        additional_capture_params = 'additional!!'

        module.capture('doesnt matter', additional_capture_params)

        mock_check_call.assert_called()
