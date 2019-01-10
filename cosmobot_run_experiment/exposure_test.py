import pytest
import numpy as np

from . import exposure as module

rgb_image = np.array([
    [[0.0, 0.1, 0.2], [0.1, 0.2, 0.0]],
    [[0.0, 0.1, 0.999], [0.0, 0.999, 0.999]]
])


class TestGenerateStastics():

    def test_overexposed_percent(self):
        stats = module._generate_statistics(rgb_image)
        actual_overexposed_percent = stats['overexposed_percent']
        expected_overexposed_percent = 0.25
        assert actual_overexposed_percent == expected_overexposed_percent

    def test_underexposed_percent(self):
        stats = module._generate_statistics(rgb_image)
        actual_underexposed_percent = stats['underexposed_percent']
        expected_underexposed_percent = 0.3333333333333333
        assert actual_underexposed_percent == expected_underexposed_percent

    @pytest.mark.parametrize("name, color_channel_key, expected_invalid_exposure_percent", [
        ('R channel', "overexposed_percent_r", 0.0),
        ('G channel', "overexposed_percent_g", 0.25),
        ('B channel', "overexposed_percent_b", 0.5),
        ('R channel', "underexposed_percent_r", 0.75),
        ('G channel', "underexposed_percent_g", 0.0),
        ('B channel', "underexposed_percent_b", 0.25)
    ])
    def test_exposure_percent_by_color_channel(
        self,
        name,
        color_channel_key,
        expected_invalid_exposure_percent
    ):
        stats = module._generate_statistics(rgb_image)
        actual_invalid_exposure_percent = stats[color_channel_key]
        assert actual_invalid_exposure_percent == expected_invalid_exposure_percent


# class TestReviewExposureStatistics:
