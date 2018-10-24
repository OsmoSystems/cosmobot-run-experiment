import pytest

from . import prepare as module


@pytest.mark.parametrize("hostname,expected_is_valid", [
    ('pi-cam-CF22', True),
    ('pi-cam-4321', True),
    ('sneaky-pi-cam-CF22', False),
    ('pi-cam-12345', False),
    ('pi-cam-1234-and-more', False),
    ('I am a naughty hostname', False),
])
def test_hostname_is_valid(hostname, expected_is_valid):
    assert module.hostname_is_valid(hostname) == expected_is_valid


class TestGetExperimentVariants():
    def test_exposure_no_iso_uses_default_iso(self):
        args = {
            'name': 'test',
            'interval': 10,
            'variant': [],
            'exposures': [100, 200],
            'isos': None
        }

        expected = [
            module.ExperimentVariant(capture_params='" -ss 100 -ISO 100 -q 100 -awb off -awbg 1.307,1.615"'),
            module.ExperimentVariant(capture_params='" -ss 200 -ISO 100 -q 100 -awb off -awbg 1.307,1.615"')
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected

    def test_exposure_and_iso_generate_correct_variants(self):
        args = {
            'name': 'test',
            'interval': 10,
            'variant': [],
            'exposures': [100, 200],
            'isos': [100, 200]
        }

        expected = [
            module.ExperimentVariant(capture_params='" -ss 100 -ISO 100 -q 100 -awb off -awbg 1.307,1.615"'),
            module.ExperimentVariant(capture_params='" -ss 100 -ISO 200 -q 100 -awb off -awbg 1.307,1.615"'),
            module.ExperimentVariant(capture_params='" -ss 200 -ISO 100 -q 100 -awb off -awbg 1.307,1.615"'),
            module.ExperimentVariant(capture_params='" -ss 200 -ISO 200 -q 100 -awb off -awbg 1.307,1.615"')
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected

    def test_exposure_and_iso_and_variant_generate_correct_variants(self):
        args = {
            'name': 'test',
            'interval': 10,
            'variant': [' -ss 4000000 -ISO 100'],
            'exposures': [100, 200],
            'isos': [100, 200]
        }

        expected = [
            module.ExperimentVariant(capture_params=' -ss 4000000 -ISO 100'),
            module.ExperimentVariant(capture_params='" -ss 100 -ISO 100 -q 100 -awb off -awbg 1.307,1.615"'),
            module.ExperimentVariant(capture_params='" -ss 100 -ISO 200 -q 100 -awb off -awbg 1.307,1.615"'),
            module.ExperimentVariant(capture_params='" -ss 200 -ISO 100 -q 100 -awb off -awbg 1.307,1.615"'),
            module.ExperimentVariant(capture_params='" -ss 200 -ISO 200 -q 100 -awb off -awbg 1.307,1.615"')
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected

    def test_only_variants_generate_correct_variants(self):
        args = {
            'name': 'test',
            'interval': 10,
            'variant': [' -ss 1000000 -ISO 100', ' -ss 1100000 -ISO 100'],
            'exposures': None,
            'isos': None
        }

        expected = [
            module.ExperimentVariant(capture_params=' -ss 1000000 -ISO 100'),
            module.ExperimentVariant(capture_params=' -ss 1100000 -ISO 100')
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected

    def test_default_variants_generated(self):
        args = {
            'name': 'test',
            'interval': 10,
            'variant': [],
            'exposures': None,
            'isos': None
        }

        expected = [
            module.ExperimentVariant(capture_params=' -ss 1500000 -ISO 100 -q 100 -awb off -awbg 1.307,1.615')
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected
