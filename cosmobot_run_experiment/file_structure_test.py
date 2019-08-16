from datetime import datetime

import pytest

from cosmobot_run_experiment.prepare import ExperimentVariant
from . import file_structure as module


class TestIsoDatetimeForFilename:
    def test_returns_iso_ish_string(self):
        actual = module.iso_datetime_for_filename(datetime(2018, 1, 2, 13, 14, 15))
        expected = "2018-01-02--13-14-15"

        assert actual == expected


class TestProcessParamStringsForFilename:
    def test_replaces_spaces(self):
        assert (
            module._process_param_for_filename("test this thing") == "test_this_thing"
        )

    def test_removes_dashes(self):
        assert module._process_param_for_filename("test-this-thing") == "testthisthing"

    def test_handles_float(self):
        assert module._process_param_for_filename(0.0) == "0.0"

    def test_handles_int(self):
        assert module._process_param_for_filename(0) == "0"

    def test_blows_up_with_unhandled_type(self):
        with pytest.raises(TypeError):
            module._process_param_for_filename({"I am": "a dictionary!!!"})


class TestGetImageFilename:
    example_variant = ExperimentVariant(
        capture_params="-br 99 -ISO 5678",
        exposure_time=1,
        camera_warm_up=5.0001,
        led_on=True,
    )
    datetime_ = datetime(2019, 4, 8, 9, 52, 12)

    def test_get_image_filename_includes_datetime(self):
        iso_ish_datetime = module.iso_datetime_for_filename(self.datetime_)
        assert iso_ish_datetime in module.get_image_filename(
            self.datetime_, self.example_variant
        )

    def test_get_image_filename_includes_capture_params_with_spaces_replaced(self):
        assert "_br_99_ISO_5678_" in module.get_image_filename(
            self.datetime_, self.example_variant
        )

    def test_get_image_filename_includes_variant_params(self):
        expected_led_params_string = (
            "_exposure_time_1_camera_warm_up_5.0001_led_on_True"
        )
        assert expected_led_params_string in module.get_image_filename(
            self.datetime_, self.example_variant
        )

    def test_get_image_filename_ends_with_underscore(self):
        # This is so that if certain capture params are missing, you can still grep in filenames for a particular
        # capture param -- eg. you can grep for "iso_100_" and have it not match iso_1000 variants as well.
        assert module.get_image_filename(self.datetime_, self.example_variant).endswith(
            "_.jpeg"
        )


# COPY-PASTA from cosmobot-process-experiment
class TestIsoDatetimeAndRestFromFilename:
    def test_returns_datetime(self):
        actual = module.datetime_from_filename(
            "2018-01-02--13-14-15-something-something.jpeg"
        )
        expected = datetime(2018, 1, 2, 13, 14, 15)

        assert actual == expected


# COPY-PASTA from cosmobot-process-experiment
class TestFilenameHasFormat:
    @pytest.mark.parametrize(
        "filename, truthiness",
        [
            ("2018-01-02--13-14-15-something-something.jpeg", True),
            ("2018-01-02--13-aa-15-something-something.jpeg", False),
            ("2018-01-02--13-14-1-hi-hi.jpeg", False),
            ("prefix-2018-01-02--13-14-15something-something.jpeg", False),
        ],
    )
    def test_filename_has_correct_datetime_format(self, filename, truthiness):
        assert module.filename_has_correct_datetime_format(filename) is truthiness
