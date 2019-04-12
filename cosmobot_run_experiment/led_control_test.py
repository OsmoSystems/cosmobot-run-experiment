from unittest.mock import sentinel
import pytest
from . import led_control as module


@pytest.fixture
def mock_show_pixels(mocker):
    return mocker.patch.object(module, 'show_pixels')


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


class TestShowPixels:
    def test_show_pixels(self, mock_adjust_color_intensity):
        color = (255, 0, 255)
        intensity = 0.5
        use_one_led = False

        module.show_pixels(color=color, intensity=intensity, use_one_led=use_one_led)
        mock_adjust_color_intensity.assert_called_with(color, intensity)

    def test_controls_neopixel_leds(self, mock_control_neopixel_leds, mock_control_digitalio_led):
        color = module.NAMED_COLORS_IN_RGB['white']
        intensity = 0.5
        module.show_pixels(color=color, intensity=intensity, use_one_led=sentinel.use_one_led)

        mock_control_neopixel_leds.assert_called_with(color, 0.5, sentinel.use_one_led)

    @pytest.mark.parametrize('name, intensity, expected', [
        ('intensity=0 turns off LED', 0, False),
        ('intensity>0 turns on LED', 0.5, True),
        ('intensity=1 turns on LED', 1, True),
        # ('intensity=2 turns on LED', 2, False),
    ])
    def test_controls_digital_LED_based_on_intensity(
        self,
        name,
        intensity,
        expected,
        mock_control_neopixel_leds,
        mock_control_digitalio_led
    ):
        module.show_pixels(intensity=intensity)
        mock_control_digitalio_led.assert_called_with(on=expected)


class TestControlNeoPixelLEDs:
    def test_raises_value_error_for_invalid_color(self):
        with pytest.raises(ValueError):
            module._control_neopixel_leds(color=(0, 0))

    # def test_adjusts_color(self):
    #     mock_adjust_color_intensity.assert_called_with(color, intensity)
    #     TODO: implement


class TestControlDigitalIoLED:
    def test_control_digitalio_led(self):
        module._control_digitalio_led(on=True)
        # TODO: implement


class TestTurnOffLeds:
    def test_turn_off_leds_turns_off_led(self, mock_show_pixels):
        module.turn_off_leds()
        mock_show_pixels.assert_called_with(intensity=0)


class TestColorAdjustment:
    @pytest.mark.parametrize('name, color_to_adjust, intensity, expected_color', [
        ('color adjusted with 0% intensity', (125, 125, 0), 0.0, (0, 0, 0)),
        ('color adjusted with 100% intensity', (255, 0, 255), 1.0, (255, 0, 255)),
        ('color adjusted with 50% intensity', (0, 255, 0), 0.5, (0, 127, 0))
    ])
    def test_color_adjusted_for_intensity(self, name, color_to_adjust, intensity, expected_color):
        actual_color = module._adjust_color_intensity(color_to_adjust, intensity)
        assert actual_color == expected_color
