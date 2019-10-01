from unittest.mock import sentinel, call

import pytest
from . import led_control as module


@pytest.fixture
def mock_control_led(mocker):
    return mocker.patch.object(module, "control_led")


class TestSetLedCli:
    @pytest.mark.parametrize(
        "args_in, expected_led_on", [(["on"], True), (["off"], False)]
    )
    def test_sets_led_appropriately(self, args_in, expected_led_on, mock_control_led):
        module.set_led_cli(args_in)
        mock_control_led.assert_called_with(led_on=expected_led_on)

    @pytest.mark.parametrize(["args_in"], [([],), ([""],), (["blue"],)])
    def test_gets_mad_appropriately_with_invalid_choice(
        self, args_in, mock_control_led
    ):
        with pytest.raises(SystemExit):
            module.set_led_cli(args_in)


class TestControlLed:
    @pytest.mark.parametrize("led_setpoint", [True, False])
    def test_sets_pin(self, led_setpoint, mocker):
        mock_dio_cls = mocker.patch.object(module.digitalio, "DigitalInOut")
        mock_dio_pin = mocker.Mock()
        mock_dio_cls.return_value = mock_dio_pin

        module.control_led(led_setpoint)

        assert mock_dio_pin.value == led_setpoint

    def test_logs_pin_and_led_info(self, mocker):
        mocker.patch.object(module.digitalio, "DigitalInOut")
        mock_info_logger = mocker.patch.object(module.logging, "info")

        module.control_led(True)

        mock_info_logger.assert_has_calls(
            [call("Turning LED on"), call("Setting DIO pin 5 -> high")]
        )


class TestFlashLed:
    def test_flash_led_calls_appropriate_things(self, mocker):
        mock_control_led = mocker.patch.object(module, "control_led")
        mock_sleep = mocker.patch.object(module, "sleep")

        module.flash_led_once(
            wait_time_seconds=sentinel.wait_time, on_time_seconds=sentinel.on_time
        )

        # These calls are interleaved, but we can only assert the call ordering separately for each method
        mock_sleep.assert_has_calls(
            [call(sentinel.wait_time), call(sentinel.on_time)], any_order=False
        )
        mock_control_led.assert_has_calls([call(True), call(False)], any_order=False)
