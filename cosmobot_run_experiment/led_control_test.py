import pytest
from . import led_control as module


@pytest.fixture
def mock_show_pixels(mocker):
    mock_show_pixels = mocker.patch.object(module, '_show_pixels')
    mock_show_pixels.return_value = None
    return mock_show_pixels


class TestLed:
    @pytest.mark.parametrize("name, args_in, expected_color, expected_intensity, expected_pixel_indices", [
        ('only red color', ['--color', 'green'], (0, 255, 0), 0.0, module.ALL_PIXELS),
        (
            'red color and intensity',
            ['--color', 'red', '--intensity', '0.8'],
            (255, 0, 0),
            0.8,
            module.ALL_PIXELS
        ),
        (
            'red, one pixel and intensity',
            ['--color', 'blue', '--intensity', '0.8', '--one-led'],
            (0, 0, 255),
            0.8,
            module.ONE_PIXEL
        ),
    ])
    def test_set_led(self, name, args_in, expected_color, expected_intensity, expected_pixel_indices, mock_show_pixels):
        module.set_led(args_in)
        mock_show_pixels.assert_called_with(expected_color, expected_intensity, pixel_indices=expected_pixel_indices)
