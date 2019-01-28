import pytest
from . import led as module


@pytest.fixture
def mock_show_pixels(mocker):
    mock_show_pixels = mocker.patch.object(module, '_show_pixels')
    mock_show_pixels.return_value = None
    return mock_show_pixels


class TestLed:
    @pytest.mark.parametrize("name, args_in, expected_color, expected_intensity", [
        ('only red color', ['--color', 'red'], (0, 0, 255, 0), 1.0),
        (
            'red color and intensity',
            ['--color', 'red', '--intensity', '0.8'],
            (0, 0, 255, 0),
            0.8
        ),
    ])
    def test_set_led(self, name, args_in, expected_color, expected_intensity, mock_show_pixels):
        module.set_led(args_in)
        mock_show_pixels.assert_called_with(expected_color, expected_intensity)
