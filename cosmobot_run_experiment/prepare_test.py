import pytest

from . import prepare as module


def test_get_mac_address(mocker):
    mocker.patch.object(module, 'get_mac').return_value = 141726673902100

    actual = module._get_mac_address()
    expected = '80E6500D9A14'

    assert actual == expected


def test_get_mac_last_4(mocker):
    mocker.patch.object(module, '_get_mac_address').return_value = '80E6500D9A14'

    actual = module._get_mac_last_4()
    expected = '9A14'

    assert actual == expected


@pytest.mark.parametrize("test_name,mac_last_4,hostname,expected_is_valid", [
    ('mac last 4 match - valid', 'CF22', 'pi-cam-CF22', True),
    ('mac last 4 dont match - invalid', '1234', 'pi-cam-4321', False),
    ('mac last 5 - invalid', '2345', 'pi-cam-12345', False),
    ('extra prefix - invalid', 'CF22', 'sneaky-pi-cam-CF22', False),
    ('extra postfix - invalid', '1234', 'pi-cam-1234-and-more', False),
])
def test_hostname_is_valid(mocker, test_name, mac_last_4, hostname, expected_is_valid):
    mocker.patch.object(module, '_get_mac_last_4').return_value = mac_last_4
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
            module.ExperimentVariant(capture_params='" -ss 100 -ISO 100"'),
            module.ExperimentVariant(capture_params='" -ss 200 -ISO 100"')
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
            module.ExperimentVariant(capture_params='" -ss 100 -ISO 100"'),
            module.ExperimentVariant(capture_params='" -ss 100 -ISO 200"'),
            module.ExperimentVariant(capture_params='" -ss 200 -ISO 100"'),
            module.ExperimentVariant(capture_params='" -ss 200 -ISO 200"')
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
            module.ExperimentVariant(capture_params='" -ss 100 -ISO 100"'),
            module.ExperimentVariant(capture_params='" -ss 100 -ISO 200"'),
            module.ExperimentVariant(capture_params='" -ss 200 -ISO 100"'),
            module.ExperimentVariant(capture_params='" -ss 200 -ISO 200"')
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
            module.ExperimentVariant(capture_params=' -ss 1500000 -ISO 100')
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected
