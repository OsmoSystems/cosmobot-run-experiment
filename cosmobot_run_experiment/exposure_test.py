import pytest
import numpy as np

from . import exposure as module

rgb_image = np.array([
    [[0.0, 0.0, 0.0], [0.499999, 0.499999, 0.499999]],
    [[0.699999, 0.699999, 0.699999], [0.999999, 0.999999, 0.999999]]
])


def test_generate_statistics():
    stats = module._generate_statistics(rgb_image)

    actual_overexposed_percent = stats['overexposed_percent']
    actual_underexposed_percent = stats['underexposed_percent']

    expected_overexposed_percent = 0.25
    expected_underexposed_percent = 0.25

    assert actual_overexposed_percent == expected_overexposed_percent
    assert actual_underexposed_percent == expected_underexposed_percent
