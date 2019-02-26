import os

import pytest
from . import prepare as module

from collections import namedtuple


class TestParseArgs:
    def test_all_args_parsed_appropriately(self):
        # Args in the format you'd get from sys.argv
        args_in = [
            '--name',
            'thebest',
            '--interval',
            '25',
            '--duration',
            '100',
            '--variant',
            # Note: when a quoted command-line value is read using sys.argv,
            # it's grouped into a single list item like this:
            '-ISO 100 -ss 50000',
            '--variant',
            'variant2',
            '--exposures',
            '20',
            '30',
            '--isos',
            '45',
            '55',
        ]

        expected_args_out = {
            'name': 'thebest',
            'interval': 25,
            'duration': 100,
            'variant': ['-ISO 100 -ss 50000', 'variant2'],
            'exposures': [20, 30],
            'isos': [45, 55],
            'skip_sync': False,
            'review_exposure': False,
            'erase_synced_files': False
        }
        assert module._parse_args(args_in) == expected_args_out

    def test_minimum_args_doesnt_blow_up(self):
        args_in = ['--name', 'thebest', '--interval', '500']
        module._parse_args(args_in)

    def test_missing_args_blows_up(self):
        args_in = []
        with pytest.raises(SystemExit):
            module._parse_args(args_in)


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


@pytest.mark.parametrize("test_name,mac_last_4,hostname,expected_is_correct", [
    ('mac last 4 match - valid', 'CF22', 'pi-cam-CF22', True),
    ('mac last 4 dont match - invalid', '1234', 'pi-cam-4321', False),
    ('mac last 5 - invalid', '2345', 'pi-cam-12345', False),
    ('extra prefix - invalid', 'CF22', 'sneaky-pi-cam-CF22', False),
    ('extra postfix - invalid', '1234', 'pi-cam-1234-and-more', False),
])
def test_hostname_is_correct(mocker, test_name, mac_last_4, hostname, expected_is_correct):
    mocker.patch.object(module, '_get_mac_last_4').return_value = mac_last_4
    assert module.hostname_is_correct(hostname) == expected_is_correct


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
            module.ExperimentVariant(
                capture_params=' -ss 100 -ISO 100',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            ),
            module.ExperimentVariant(
                capture_params=' -ss 200 -ISO 100',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            )
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
            module.ExperimentVariant(
                capture_params=' -ss 100 -ISO 100',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            ),
            module.ExperimentVariant(
                capture_params=' -ss 100 -ISO 200',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            ),
            module.ExperimentVariant(
                capture_params=' -ss 200 -ISO 100',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            ),
            module.ExperimentVariant(
                capture_params=' -ss 200 -ISO 200',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            )
        ]

        actual = module.get_experiment_variants(args)
        print(actual)
        print(expected)
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
            module.ExperimentVariant(
                capture_params=' -ss 4000000 -ISO 100',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            ),
            module.ExperimentVariant(
                capture_params=' -ss 100 -ISO 100',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            ),
            module.ExperimentVariant(
                capture_params=' -ss 100 -ISO 200',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            ),
            module.ExperimentVariant(
                capture_params=' -ss 200 -ISO 100',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            ),
            module.ExperimentVariant(
                capture_params=' -ss 200 -ISO 200',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            )
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
            module.ExperimentVariant(
                capture_params=' -ss 1000000 -ISO 100',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            ),
            module.ExperimentVariant(
                capture_params=' -ss 1100000 -ISO 100',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            )
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
            module.ExperimentVariant(
                capture_params=' -ss 1500000 -ISO 100',
                led_warm_up=0.0,
                led_color='white',
                led_intensity=0.0,
                use_one_led=False,
                led_cool_down=0.0
            )
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected


class TestCreateFileStructureForExperiment:
    MockExperimentConfiguration = namedtuple(
        'MockExperimentConfiguration',
        ['experiment_directory_path']
    )

    subdir_name = 'subdirectory'

    def test_mock_experiment_configuration_subset_of_real_experiment_configuration(self):
        assert set(self.MockExperimentConfiguration._fields).issubset(module.ExperimentConfiguration._fields)

    def _create_mock_configuration(self, mocker, tmp_path):
        experiment_directory_path = os.path.join(
            str(tmp_path),  # tmp_path is a PosixPath instance. python 2.5's os.path.join doesn't know how to handle it.
            self.subdir_name
        )

        return self.MockExperimentConfiguration(
            experiment_directory_path=experiment_directory_path,
        )

    def test_output_directory_present__does_not_explode(self, mocker, tmp_path):
        mock_config = self._create_mock_configuration(mocker, tmp_path)

        os.mkdir(mock_config.experiment_directory_path)

        module.create_file_structure_for_experiment(
            mock_config
        )

    def test_creates_output_directory_if_not_present(self, mocker, tmp_path):
        mock_config = self._create_mock_configuration(mocker, tmp_path)

        module.create_file_structure_for_experiment(
            mock_config
        )

        assert os.path.exists(mock_config.experiment_directory_path)

    def test_creates_metadata_file_in_output_directory(self, mocker, tmp_path):
        mock_config = self._create_mock_configuration(mocker, tmp_path)

        module.create_file_structure_for_experiment(
            mock_config
        )

        assert os.listdir(mock_config.experiment_directory_path) == ['experiment_metadata.yml']
