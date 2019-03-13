import pytest
from . import led_control as module


@pytest.fixture
def mock_show_pixels(mocker):
    mock_show_pixels = mocker.patch.object(module, 'show_pixels')
    return mock_show_pixels


class TestColorAdjustment:
    @pytest.mark.parametrize('name, color_to_adjust, intensity, expected_color', [
        ((125, 125, 0), 0.0, (0, 0, 0)),
        ((255, 0, 255), 1.0, (255, 0, 255)),
        ((0, 255, 0), 0.5, (0, 127, 0))
    ])
    def test_color_adjusted_for_intensity(self, color_tuple, intensity, expected_color):
        actual_color = module.color_adjusted_for_intensity(color_tuple, intensity)
        assert actual_color == expected_color


class TestLed:
    @pytest.mark.parametrize('name, args_in, expected_color, expected_intensity, expected_use_one_led', [
        (
            'only red color at 0.0 intensity for one pixel',
            ['--color', 'green', '--use-one-led'],
            (0, 255, 0),
            0.0,
            True
        ),
        (
            'red color and intensity of 0.8 for one pixel',
            ['--color', 'red', '--intensity', '0.8', '--use-one-led'],
            (255, 0, 0),
            0.8,
            True
        ),
        (
            'blue, intensity of 0.8 for all pixels',
            ['--color', 'blue', '--intensity', '0.8'],
            (0, 0, 255),
            0.8,
            False
        ),
    ])
    def test_set_led(
            self,
            name,
            args_in,
            expected_color,
            expected_intensity,
            expected_use_one_led,
            mock_show_pixels
    ):
        module.set_led(args_in)
        mock_show_pixels.assert_called_with(
            color=expected_color,
            intensity=expected_intensity,
            use_one_led=expected_use_one_led
        )

    def test_turn_off_leds_turns_off_led(self, mock_show_pixels):
        module.turn_off_leds()
        mock_show_pixels.assert_called_with(intensity=0)
