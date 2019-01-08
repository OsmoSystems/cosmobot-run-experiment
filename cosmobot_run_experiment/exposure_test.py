import pytest
import numpy as np

from . import exposure as module

rgb_image = np.array([
    [[0.0, 0.0, 0.0], [0.499999, 0.499999, 0.499999]],
    [[0.699999, 0.699999, 0.699999], [0.999999, 0.999999, 0.999999]]
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
        expected_underexposed_percent = 0.25
        assert actual_underexposed_percent == expected_underexposed_percent

    @pytest.mark.parametrize("name, color_channel_index, expected_color_channel_overexposed_percent", [
        ('R channel', "overexposed_percent_r", 0.25),
        ('G channel', "overexposed_percent_g", 0.25),
        ('B channel', "overexposed_percent_b", 0.25)
    ])
    def test_underexposed_percent_by_color_channel(self, name, color_channel_index, expected_color_channel_overexposed_percent):
        stats = module._generate_statistics(rgb_image)
        actual_color_channel_overexposed_percent = stats[color_channel_index]
        assert actual_color_channel_overexposed_percent == expected_color_channel_overexposed_percent
