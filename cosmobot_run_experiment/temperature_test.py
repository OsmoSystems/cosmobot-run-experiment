import csv
import os
from unittest.mock import sentinel, Mock

import pytest

from . import temperature as module


@pytest.fixture
def mock_initialize_temperature_adc(mocker):
    return mocker.patch.object(module, '_initialize_temperature_adc')


class TestGetOrInitializeTemperatureAdc:
    def teardown(self):
        # Reset global variable between tests
        module._temperature_adc_channel = None

    def test_initilizes_on_first_call(self, mock_initialize_temperature_adc):
        assert module._temperature_adc_channel is None

        actual_temperature_adc_channel = module._get_or_initialize_temperature_adc()

        assert mock_initialize_temperature_adc.call_count == 1
        assert module._temperature_adc_channel is not None
        assert module._temperature_adc_channel == actual_temperature_adc_channel

    def test_does_not_initialize_on_second_call(self, mock_initialize_temperature_adc):
        assert module._temperature_adc_channel is None

        module._get_or_initialize_temperature_adc()
        actual_temperature_adc_channel = module._get_or_initialize_temperature_adc()

        assert mock_initialize_temperature_adc.call_count == 1
        assert module._temperature_adc_channel is not None
        assert module._temperature_adc_channel == actual_temperature_adc_channel


class TestReadTemperature:
    def test_returns_temperature_reading(self, mocker):
        mocker.patch.object(module, '_get_or_initialize_temperature_adc').side_effect = lambda: Mock(
            value=sentinel.digital_count,
            voltage=sentinel.voltage,
        )

        actual = module.read_temperature(sentinel.capture_timestamp)

        expected = module.TemperatureReading(
            capture_timestamp=sentinel.capture_timestamp,
            digital_count=sentinel.digital_count,
            voltage=sentinel.voltage
        )

        assert actual == expected


class TestGetOrCreateTemperatureLog:
    def test_does_not_create_or_update_file_if_exists(self, tmp_path):
        # tmp_path is a PosixPath instance. Python 3.5's os.path.join doesn't know how to handle it.
        mock_experiment_directory = str(tmp_path)

        # Create a mock pre-existing log file with a mock header
        mock_log_filepath = os.path.join(mock_experiment_directory, module.TEMPERATURE_LOG_FILENAME)
        mock_header = u'mock header'
        with open(mock_log_filepath, 'w') as f:
            f.write(mock_header)

        actual_log_path = module._get_or_create_temperature_log(experiment_directory=mock_experiment_directory)

        with open(actual_log_path, 'r') as f:
            assert f.read() == mock_header

    def test_creates_file_with_header_if_not_exists(self, tmp_path):
        # tmp_path is a PosixPath instance. Python 3.5's os.path.join doesn't know how to handle it.
        mock_experiment_directory = str(tmp_path)

        actual_log_filepath = module._get_or_create_temperature_log(experiment_directory=mock_experiment_directory)
        expected_log_filepath = os.path.join(mock_experiment_directory, module.TEMPERATURE_LOG_FILENAME)

        assert actual_log_filepath == expected_log_filepath
        with open(actual_log_filepath, 'r') as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == list(module.TemperatureReading._fields)


MOCK_DIGITAL_COUNT = 12345
MOCK_VOLTAGE = 0.12345


def _mock_read_temperature(capture_timestamp):
    return module.TemperatureReading(
        capture_timestamp=capture_timestamp,
        digital_count=MOCK_DIGITAL_COUNT,
        voltage=MOCK_VOLTAGE
    )


@pytest.fixture
def mock_read_temperature(mocker):
    mock_read_temperature = mocker.patch.object(module, 'read_temperature')
    mock_read_temperature.side_effect = _mock_read_temperature

    return mock_read_temperature


class TestLogTemperature:
    def test_appends_temperature_reading_rows(self, tmp_path, mock_read_temperature):
        # tmp_path is a PosixPath instance. Python 3.5's os.path.join doesn't know how to handle it.
        mock_experiment_directory = str(tmp_path)

        module.log_temperature(
            experiment_directory=mock_experiment_directory,
            capture_time='2019-01-01'
        )

        actual_log_filepath = module.log_temperature(
            experiment_directory=mock_experiment_directory,
            capture_time='2019-01-02'
        )

        with open(actual_log_filepath, 'r') as f:
            readings = list(csv.DictReader(f))

            assert dict(readings[0]) == {
                'capture_timestamp': '2019-01-01',
                'digital_count': str(MOCK_DIGITAL_COUNT),
                'voltage': str(MOCK_VOLTAGE),
            }

            assert dict(readings[1]) == {
                'capture_timestamp': '2019-01-02',
                'digital_count': str(MOCK_DIGITAL_COUNT),
                'voltage': str(MOCK_VOLTAGE),
            }
