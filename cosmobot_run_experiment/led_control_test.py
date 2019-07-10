import pytest
from . import led_control as module


@pytest.fixture
def mock_control_led(mocker):
    return mocker.patch.object(module, "control_led")


class TestMain:
    @pytest.mark.parametrize(
        "args_in, expected_led_on", [(["on"], True), (["off"], False)]
    )
    def test_sets_led_appropriately(self, args_in, expected_led_on, mock_control_led):
        module.main(args_in)
        mock_control_led.assert_called_with(led_on=expected_led_on)

    @pytest.mark.parametrize(["args_in"], [([],), ([""],), (["blue"],)])
    def test_gets_mad_appropriately_with_invalid_choice(
        self, args_in, mock_control_led
    ):
        with pytest.raises(SystemExit):
            module.main(args_in)


class TestControlLed:
    @pytest.mark.parametrize("led_setpoint", [True, False])
    def test_sets_inverse_value(self, led_setpoint, mocker):
        mock_dio_cls = mocker.patch.object(module.digitalio, "DigitalInOut")
        mock_dio_pin = mocker.Mock()
        mock_dio_cls.return_value = mock_dio_pin

        module.control_led(led_setpoint)

        # the LED is wired such that when the pin is HIGH, the LED is off and vice versa.
        expected_pin_value = not led_setpoint

        assert mock_dio_pin.value == expected_pin_value

    def test_logs_pin_and_led_info(self, mocker):
        mocker.patch.object(module.digitalio, "DigitalInOut")
        mock_info_logger = mocker.patch.object(module.logging, "info")

        module.control_led(True)

        mock_info_logger.assert_called_with("Turning LED on (DIO pin 6 -> low)")
