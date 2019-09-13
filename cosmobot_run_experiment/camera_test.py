import pytest
from unittest.mock import Mock

from . import camera as module


class TestCaptureWithPiCamera:
    def test_sets_default_attributes(self):
        mock_camera = Mock()
        module.capture_with_picamera(camera=mock_camera, image_filepath="foo.jpeg")

        assert mock_camera.iso == 100
        assert mock_camera.resolution == (3280, 2464)
        assert mock_camera.awb_mode == "off"
        assert mock_camera.awb_gains == (1.307, 1.615)

    def test_sets_shutter_speed_and_framerate_based_on_exposure_time(self):
        mock_camera = Mock()
        module.capture_with_picamera(
            camera=mock_camera, image_filepath="foo.jpeg", exposure_time=2 / 9
        )

        assert mock_camera.framerate == 9 / 2
        assert mock_camera.shutter_speed == 222222

    def test_captures_as_bayer_with_quality_jpeg(self):
        mock_capture = Mock()
        mock_camera = Mock(capture=mock_capture)
        module.capture_with_picamera(
            camera=mock_camera, image_filepath="foo.jpeg", quality=1000
        )

        mock_capture.assert_called_with("foo.jpeg", bayer=True, quality=1000)


class TestCaptureWithRaspistill:
    def test_makes_expected_call_with_minimal_params(self, mocker):
        mock_check_call = mocker.patch.object(module, "check_call")

        filename = "output_file.jpeg"
        expected_command = (
            'raspistill --raw -o "output_file.jpeg"'
            " -q 100 -awb off -awbg 1.307,1.615 -ss 800000 -ISO 100 --timeout 5000 "
        )

        module.capture_with_raspistill(filename)

        expected_call = mocker.call(expected_command, shell=True)

        mock_check_call.assert_has_calls([expected_call])

    def test_rounds_non_integer_exposure_time(self, mocker):
        mock_check_call = mocker.patch.object(module, "check_call")

        filename = "output_file.jpeg"
        expected_command = (
            'raspistill --raw -o "output_file.jpeg"'
            " -q 100 -awb off -awbg 1.307,1.615 -ss 333333 -ISO 100 --timeout 5000 "
        )

        module.capture_with_raspistill(filename, exposure_time=1 / 3)

        expected_call = mocker.call(expected_command, shell=True)

        mock_check_call.assert_has_calls([expected_call])

    def test_makes_call_with_additional_capture_params_at_end(self, mocker):
        # When provided with multiple values for the same argument, raspistill appears to use the last one
        # and ignore the others. Putting additional_capture_params at the end ensures that user-provided values
        # will override the defaults.
        mock_check_call = mocker.patch.object(module, "check_call")
        additional_capture_params = "additional!!"

        module.capture_with_raspistill(
            mocker.sentinel.filename,
            additional_capture_params=additional_capture_params,
        )

        # Call args looks like [call(command, shell=True)] where call is a tuple
        actual_call_command = mock_check_call.call_args[0][0]

        padded_additional_capture_params = " {additional_capture_params}".format(
            **locals()
        )
        assert actual_call_command.endswith(padded_additional_capture_params)

    def test_blows_up_if_check_call_fails(self, mocker):
        # This is a common occurence at the start of an (attempted) experiment
        mocker.patch.object(module, "check_call").side_effect = Exception(
            "omg something else is using the camera and I don't know what to do :'(''"
        )

        with pytest.raises(Exception):
            module.capture_with_raspistill(mocker.sentinel.filename)
