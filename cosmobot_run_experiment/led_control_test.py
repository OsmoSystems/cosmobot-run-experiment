from unittest.mock import sentinel
import pytest
from . import led_control as module


@pytest.fixture
def mock_control_leds(mocker):
    return mocker.patch.object(module, 'control_leds')


@pytest.fixture
def mock_control_neopixel_leds(mocker):
    return mocker.patch.object(module, '_control_neopixel_leds')


@pytest.fixture
def mock_control_digitalio_led(mocker):
    return mocker.patch.object(module, '_control_digitalio_led')


@pytest.fixture
def mock_adjust_color_intensity(mocker):
    mock_adjust_color_intensity = mocker.patch.object(module, '_adjust_color_intensity')
    return mock_adjust_color_intensity


class TestSetLed:
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
    def test_set_led(self, name, args_in, expected_color, expected_intensity, expected_use_one_led, mock_control_leds):
        module.set_led(args_in)
        mock_control_leds.assert_called_with(
            color=expected_color,
            intensity=expected_intensity,
            use_one_led=expected_use_one_led
        )


class TestControlLeds:
    def test_controls_neopixel_leds(self, mock_control_neopixel_leds, mock_control_digitalio_led):
        color = module.NAMED_COLORS_IN_RGB['white']
        intensity = 0.5

        module.control_leds(color=color, intensity=intensity, use_one_led=sentinel.use_one_led)

        mock_control_neopixel_leds.assert_called_with(color, intensity, sentinel.use_one_led)

    @pytest.mark.parametrize('name, intensity, on', [
        ('intensity=0 turns off LED', 0, False),
        ('intensity>0 turns on LED', 0.5, True),
        ('intensity=1 turns on LED', 1, True),
    ])
    def test_controls_digital_led(self, name, intensity, on, mock_control_neopixel_leds, mock_control_digitalio_led):
        module.control_leds(intensity=intensity)

        mock_control_digitalio_led.assert_called_with(on=on)


class TestControlNeoPixelLEDs:
    def test_raises_value_error_for_invalid_color(self):
        with pytest.raises(ValueError):
            module._control_neopixel_leds(color=(0, 0))

    def test_does_not_raise_for_valid_color(self):
        module._control_neopixel_leds(color=module.NAMED_COLORS_IN_RGB['white'])

    def test_adjusts_color(self, mock_adjust_color_intensity):
        color = module.NAMED_COLORS_IN_RGB['white']
        module._control_neopixel_leds(color, sentinel.intensity)
        mock_adjust_color_intensity.assert_called_with(color, sentinel.intensity)

    def test_sets_pixels(self):
        # TODO: implement
        pass


class TestTurnOffLeds:
    def test_turn_off_leds_turns_off_led(self, mock_control_leds):
        module.turn_off_leds()
        mock_control_leds.assert_called_with(intensity=0)


class TestAdjustColorIntensity:
    @pytest.mark.parametrize('name, color_to_adjust, intensity, expected_color', [
        ('color adjusted with 0% intensity', (125, 125, 0), 0.0, (0, 0, 0)),
        ('color adjusted with 100% intensity', (255, 0, 255), 1.0, (255, 0, 255)),
        ('color adjusted with 50% intensity', (0, 255, 0), 0.5, (0, 127, 0))
    ])
    def test_color_adjusted_for_intensity(self, name, color_to_adjust, intensity, expected_color):
        actual_color = module._adjust_color_intensity(color_to_adjust, intensity)
        assert actual_color == expected_color
