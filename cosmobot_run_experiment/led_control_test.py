import pytest
from . import led_control as module


@pytest.fixture
def mock_control_led(mocker):
    return mocker.patch.object(module, 'control_led')


class TestMain:
    @pytest.mark.parametrize('args_in, expected_led_on', [
        (
            ['on'],
            True
        ),
        (
            ['off'],
            False
        ),
    ])
    def test_sets_led_appropriately(self, args_in, expected_led_on, mock_control_led):
        module.main(args_in)
        mock_control_led.assert_called_with(
            on=expected_led_on
        )

    @pytest.mark.parametrize(['args_in'], [
        ([],),
        ([''],),
        (['blue'],),
    ])
    def test_gets_mad_appropriately_with_invalid_choice(self, args_in, mock_control_led):
        with pytest.raises(SystemExit):
            module.main(args_in)
