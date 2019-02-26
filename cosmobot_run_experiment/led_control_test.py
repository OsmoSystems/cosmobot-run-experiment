import pytest
from . import led_control as module


@pytest.fixture
def mock_show_pixels(mocker):
    mock_show_pixels = mocker.patch.object(module, 'show_pixels')
    mock_show_pixels.return_value = None
    return mock_show_pixels


class TestLed:
    @pytest.mark.parametrize("name, args_in, expected_color, expected_intensity, expected_use_one_led", [
        ('only red color', ['--color', 'green', '--use-one-led'], (0, 255, 0), 0.0, True),
        (
            'red color and intensity',
            ['--color', 'red', '--intensity', '0.8', '--use-one-led'],
            (255, 0, 0),
            0.8,
            True
        ),
        (
            'red, one pixel and intensity',
            ['--color', 'blue', '--intensity', '0.8'],
            (0, 0, 255),
            0.8,
            False
        ),
    ])
    def test_set_led(self, name, args_in, expected_color, expected_intensity, expected_use_one_led, mock_show_pixels):
        module.set_led(args_in)
        mock_show_pixels.assert_called_with(expected_color, expected_intensity, use_one_led=expected_use_one_led)
