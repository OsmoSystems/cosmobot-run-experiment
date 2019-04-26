import pytest
from . import led_control as module


@pytest.fixture
def mock_control_led(mocker):
    return mocker.patch.object(module, 'control_led')


class TestSetLed:
    @pytest.mark.parametrize('args_in, expected_led_on', [
        (
            ['--on'],
            True
        ),
        (
            [],
            False
        ),
    ])
    def test_set_led(self, args_in, expected_led_on, mock_control_led):
        module.main(args_in)
        mock_control_led.assert_called_with(
            on=expected_led_on
        )
