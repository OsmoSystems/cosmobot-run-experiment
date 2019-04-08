from datetime import datetime

import pytest

from cosmobot_run_experiment.prepare import ExperimentVariant
from . import file_structure as module


class TestIsoDatetimeForFilename:
    def test_returns_iso_ish_string(self):
        actual = module.iso_datetime_for_filename(datetime(2018, 1, 2, 13, 14, 15))
        expected = '2018-01-02--13-14-15'

        assert actual == expected


class TestProcessParamStringsForFilename:
    def test_replaces_spaces(self):
        assert module._process_param_for_filename('test this thing') == 'test_this_thing'

    def test_removes_dashes(self):
        assert module._process_param_for_filename('test-this-thing') == 'testthisthing'

    def test_handles_float(self):
        assert module._process_param_for_filename(0.0) == '0.0'

    def test_handles_int(self):
        assert module._process_param_for_filename(0.0) == '0.0'

    def test_blows_up_with_unhandled_type(self):
        with pytest.raises(TypeError):
            module._process_param_for_filename({'I am': 'a dictionary!!!'})


class TestGetImageFilename:
    example_variant = ExperimentVariant(
        capture_params=' -ss 1234 -ISO 5678',
        led_warm_up=0.1,
        led_color='red',
        led_intensity=1.0,
        use_one_led=True,
        led_cool_down=99,
    )
    datetime_ = datetime(2019, 4, 8, 9, 52, 12)

    def test_get_image_filename_includes_datetime(self):
        assert '2019' in module.get_image_filename(self.datetime_, self.example_variant)

    def test_get_image_filename_includes_capture_params_with_spaces_replaced(self):
        assert '_ss_1234_ISO_5678_' in module.get_image_filename(self.datetime_, self.example_variant)

    def test_get_image_filename_includes_led_capture_params(self):
        expected_led_params_string = (
            'led_warm_up_0.1_led_color_red_led_intensity_1.0_use_one_led_True_led_cool_down_99'
        )
        assert expected_led_params_string in module.get_image_filename(self.datetime_, self.example_variant)

    def test_get_image_filename_ends_with_underscore(self):
        # This is so that if certain capture params are missing, you can still grep in filenames for a particular
        # capture param -- eg. you can grep for "iso_100_" and have it not match iso_1000 variants as well.
        assert module.get_image_filename(self.datetime_, self.example_variant).endswith('_.jpeg')
