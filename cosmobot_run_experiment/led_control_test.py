import pytest
from . import led_control as module


@pytest.fixture
def mock_show_pixels(mocker):
    mock_show_pixels = mocker.patch.object(module, 'show_pixels')
    return mock_show_pixels

@pytest.fixture
def mock_color_adjusted_for_intensity(mocker):
    mock_color_adjusted_for_intensity = mocker.patch.object(module, 'color_adjusted_for_intensity')
    return mock_color_adjusted_for_intensity


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

    def test_show_pixels(self, mock_color_adjusted_for_intensity):
        color = (255, 0, 255)
        intensity = 0.5
        use_one_led = False

        module.show_pixels(color=color, intensity=intensity, use_one_led=use_one_led)
        mock_color_adjusted_for_intensity.assert_called_with(color, intensity)


        assert True;

    def test_turn_off_leds_turns_off_led(self, mock_show_pixels):
        module.turn_off_leds()
        mock_show_pixels.assert_called_with(intensity=0)

    def test_show_pixels_raises_value_error(self):
        with pytest.raises(ValueError) as value_error:
            module.show_pixels(color=(0,0))


class TestColorAdjustment:
    @pytest.mark.parametrize('name, color_to_adjust, intensity, expected_color', [
        ('color adjusted with 0% intensity', (125, 125, 0), 0.0, (0, 0, 0)),
        ('color adjusted with 100% intensity', (255, 0, 255), 1.0, (255, 0, 255)),
        ('color adjusted with 50% intensity', (0, 255, 0), 0.5, (0, 127, 0))
    ])
    def test_color_adjusted_for_intensity(self, name, color_to_adjust, intensity, expected_color):
        actual_color = module.color_adjusted_for_intensity(color_to_adjust, intensity)
        assert actual_color == expected_color
