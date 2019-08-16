import datetime
import os
from unittest.mock import sentinel

import pytest
from . import prepare as module

from collections import namedtuple


class TestParseArgs:
    def test_all_args_parsed_appropriately(self):
        # Args in the format you'd get from sys.argv
        args_in = [
            "--name",
            "thebest",
            "--interval",
            "25",
            "--duration",
            "100",
            "--variant",
            # Note: when a quoted command-line value is read using sys.argv,
            # it's grouped into a single list item like this:
            "-ISO 100",
            "--variant",
            "variant2",
            "--exposures",
            "20",
            "30",
            "--isos",
            "45",
            "55",
            "--raspistill-load-time",
            "2",
        ]

        expected_args_out = {
            "name": "thebest",
            "interval": 25,
            "duration": 100,
            "variant": ["-ISO 100", "variant2"],
            "exposures": [20, 30],
            "isos": [45, 55],
            "skip_temperature": False,
            "skip_sync": False,
            "review_exposure": False,
            "erase_synced_files": False,
            "group_results": False,
            "raspistill_load_time": 2,
        }
        assert module._parse_args(args_in) == expected_args_out

    def test_minimum_args_doesnt_blow_up(self):
        args_in = ["--name", "thebest", "--interval", "500"]
        module._parse_args(args_in)

    def test_missing_args_blows_up(self):
        args_in = []
        with pytest.raises(SystemExit):
            module._parse_args(args_in)

    def test_group_results_and_skip_sync_exclusive(self):
        args_in = [
            "--name",
            "thebest",
            "--interval",
            "500",
            "--group-results",
            "--skip-sync",
        ]
        with pytest.raises(SystemExit):
            module._parse_args(args_in)


def test_get_mac_address(mocker):
    mocker.patch.object(module, "get_mac").return_value = 141726673902100

    actual = module._get_mac_address()
    expected = "80E6500D9A14"

    assert actual == expected


def test_get_mac_last_4(mocker):
    mocker.patch.object(module, "_get_mac_address").return_value = "80E6500D9A14"

    actual = module._get_mac_last_4()
    expected = "9A14"

    assert actual == expected


@pytest.mark.parametrize(
    "test_name,mac_last_4,hostname,expected_is_correct",
    [
        ("mac last 4 match - valid", "CF22", "pi-cam-CF22", True),
        ("mac last 4 dont match - invalid", "1234", "pi-cam-4321", False),
        ("mac last 5 - invalid", "2345", "pi-cam-12345", False),
        ("extra prefix - invalid", "CF22", "sneaky-pi-cam-CF22", False),
        ("extra postfix - invalid", "1234", "pi-cam-1234-and-more", False),
    ],
)
def test_hostname_is_correct(
    mocker, test_name, mac_last_4, hostname, expected_is_correct
):
    mocker.patch.object(module, "_get_mac_last_4").return_value = mac_last_4
    assert module.hostname_is_correct(hostname) == expected_is_correct


def _default_variant_with(**kwargs):
    """ get an ExperimentVariant with overridable default settings """
    variant_kwargs = {
        "capture_params": "",
        "exposure_time": 1.5,
        "camera_warm_up": 5,
        "led_on": False,
        "led_warm_up": 0.2,
        "led_buffer": 0.2,
        **kwargs,
    }
    return module.ExperimentVariant(**variant_kwargs)


class TestGetExperimentVariants:
    def test_exposure_no_iso_uses_default_iso(self):
        args = {
            "name": "test",
            "interval": 10,
            "variant": [],
            "exposures": [1, 2],
            "isos": None,
        }

        expected = [
            _default_variant_with(capture_params="-ISO 100", exposure_time=1),
            _default_variant_with(capture_params="-ISO 100", exposure_time=2),
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected

    def test_exposure_and_iso_generate_correct_variants(self):
        args = {
            "name": "test",
            "interval": 10,
            "variant": [],
            "exposures": [1, 2],
            "isos": [100, 200],
        }

        expected = [
            _default_variant_with(capture_params="-ISO 100", exposure_time=1),
            _default_variant_with(capture_params="-ISO 200", exposure_time=1),
            _default_variant_with(capture_params="-ISO 100", exposure_time=2),
            _default_variant_with(capture_params="-ISO 200", exposure_time=2),
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected

    def test_exposure_and_iso_and_variant_generate_correct_variants(self):
        args = {
            "name": "test",
            "interval": 10,
            "variant": ["--exposure-time 0.4 -ISO 100"],
            "exposures": [1, 2.5],
            "isos": [100, 200],
        }

        expected = [
            _default_variant_with(capture_params="-ISO 100", exposure_time=0.4),
            _default_variant_with(capture_params="-ISO 100", exposure_time=1),
            _default_variant_with(capture_params="-ISO 200", exposure_time=1),
            _default_variant_with(capture_params="-ISO 100", exposure_time=2.5),
            _default_variant_with(capture_params="-ISO 200", exposure_time=2.5),
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected

    def test_only_variants_generate_correct_variants(self):
        args = {
            "name": "test",
            "interval": 10,
            "variant": [" -ISO 100", " -ISO 200"],
            "exposures": None,
            "isos": None,
        }

        expected = [
            _default_variant_with(capture_params="-ISO 100"),
            _default_variant_with(capture_params="-ISO 200"),
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected

    def test_led_params_passed_through(self):
        args = {
            "name": "test",
            "interval": 10,
            "variant": [" -ISO 100 --led-on --led-warm-up 1"],
            "exposures": None,
            "isos": None,
        }

        expected = [
            _default_variant_with(capture_params="-ISO 100", led_on=True, led_warm_up=1)
        ]

        actual = module.get_experiment_variants(args)
        assert actual == expected

    def test_no_variant_args_produces_default_variant(self):
        args = {
            "name": "test",
            "interval": 10,
            "variant": [],
            "exposures": None,
            "isos": None,
        }

        expected = [_default_variant_with(capture_params="-ISO 100")]

        actual = module.get_experiment_variants(args)
        assert actual == expected


class TestCreateFileStructureForExperiment:
    MockExperimentConfiguration = namedtuple(
        "MockExperimentConfiguration", ["experiment_directory_path", "start_date"]
    )

    subdir_name = "subdirectory"

    def test_mock_experiment_configuration_subset_of_real_experiment_configuration(
        self
    ):
        assert set(self.MockExperimentConfiguration._fields).issubset(
            module.ExperimentConfiguration._fields
        )

    def _create_mock_configuration(self, mocker, tmp_path):
        experiment_directory_path = os.path.join(
            str(
                tmp_path
            ),  # tmp_path is a PosixPath instance. python 3.5's os.path.join doesn't know how to handle it.
            self.subdir_name,
        )

        return self.MockExperimentConfiguration(
            experiment_directory_path=experiment_directory_path,
            start_date=datetime.datetime(year=1988, month=9, day=1),
        )

    def test_output_directory_present__does_not_explode(self, mocker, tmp_path):
        mock_config = self._create_mock_configuration(mocker, tmp_path)

        os.mkdir(mock_config.experiment_directory_path)

        module.create_file_structure_for_experiment(mock_config)

    def test_creates_output_directory_if_not_present(self, mocker, tmp_path):
        mock_config = self._create_mock_configuration(mocker, tmp_path)

        module.create_file_structure_for_experiment(mock_config)

        assert os.path.exists(mock_config.experiment_directory_path)

    def test_creates_metadata_file_in_output_directory(self, mocker, tmp_path):
        mock_config = self._create_mock_configuration(mocker, tmp_path)

        module.create_file_structure_for_experiment(mock_config)

        assert os.listdir(mock_config.experiment_directory_path) == [
            "1988-09-01--00-00-00_experiment_metadata.yml"
        ]


class TestParseVariant:
    def test_creates_variant_with_params(self):
        variant = module._parse_variant(
            "--iso 123 --exposure-time 0.4 --camera-warm-up 5 --led-on --led-warm-up 1 --led-buffer 3"
        )
        expected_variant = module.ExperimentVariant(
            capture_params="--iso 123",
            exposure_time=0.4,
            camera_warm_up=5,
            led_on=True,
            led_warm_up=1,
            led_buffer=3,
        )
        assert variant == expected_variant

    def test_creates_variant_has_sane_defaults(self):
        expected_variant = module.ExperimentVariant(
            capture_params=module.DEFAULT_CAPTURE_PARAMS,
            exposure_time=1.5,
            camera_warm_up=5,
            led_on=False,
            led_warm_up=0.2,
            led_buffer=0.2,
        )
        assert module._parse_variant("") == expected_variant

    def test_creates_variant_doesnt_allow_longer_led_warm_up_than_camera_warm_up(self):
        with pytest.raises(ValueError):
            module._parse_variant("--camera-warm-up 1 --led-warm-up 100")

    def test_doesnt_allow_old_school_shutter_speed(self):
        with pytest.raises(ValueError):
            module._parse_variant("-ss 100000000")

    def test_doesnt_allow_old_school_timeout(self):
        with pytest.raises(ValueError):
            module._parse_variant("--timeout 1")

    def test_allows_short_or_long_version_of_exposure_time_parameter(self):
        old_school = module._parse_variant("-ex 1")
        new_school = module._parse_variant("--exposure-time 1")
        assert old_school == new_school


@pytest.fixture
def mock_list_experiments(mocker):
    return mocker.patch.object(module, "list_experiments")


@pytest.fixture
def mock_get_base_output_path(mocker):
    return mocker.patch.object(
        module, "get_base_output_path", return_value="base-output-path"
    )


class TestGetExperimentDirectoryPath:
    def test_uses_matching_dir_name_for_group_results(
        self, mock_get_base_output_path, mock_list_experiments
    ):
        group_results = True
        pi_experiment_name = "Pi1234-cool_experiment"
        start_date = sentinel.start_date

        mock_list_experiments.return_value = [
            "date3-Pi1234-bad_experiment",
            "date2-{pi_experiment_name}".format(**locals()),
            "date1-{pi_experiment_name}".format(**locals()),
        ]

        actual_path = module._get_experiment_directory_path(
            group_results, pi_experiment_name, start_date
        )
        expected_path = os.path.join(
            "base-output-path", "date2-{pi_experiment_name}".format(**locals())
        )
        assert actual_path == expected_path

    def test_generates_dir_name_when_no_matching_directory_for_group_results(
        self, mock_get_base_output_path, mock_list_experiments
    ):
        group_results = True
        pi_experiment_name = "Pi1234-cool_experiment"
        start_date = datetime.datetime(year=1988, month=9, day=1)

        mock_list_experiments.return_value = [
            "date1-Pi5678-cool_experiment",
            "date2-Pi1234-bad_experiment",
        ]

        expected_path = os.path.join(
            "base-output-path",
            "1988-09-01--00-00-00-{pi_experiment_name}".format(**locals()),
        )
        actual_path = module._get_experiment_directory_path(
            group_results, pi_experiment_name, start_date
        )
        assert actual_path == expected_path

    def test_generates_dir_name_when_group_results_is_false(
        self, mock_get_base_output_path, mock_list_experiments
    ):
        group_results = False
        pi_experiment_name = "Pi1234-cool_experiment"
        start_date = datetime.datetime(year=1988, month=9, day=1)

        expected_path = os.path.join(
            "base-output-path",
            "1988-09-01--00-00-00-{pi_experiment_name}".format(**locals()),
        )
        actual_path = module._get_experiment_directory_path(
            group_results, pi_experiment_name, start_date
        )
        assert actual_path == expected_path
        mock_list_experiments.assert_not_called()
