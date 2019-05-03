import csv
from datetime import datetime
import os
from unittest.mock import sentinel, Mock

import pytest

from . import temperature as module


@pytest.fixture
def mock_initialize_temperature_adc(mocker):
    return mocker.patch.object(module, '_initialize_temperature_adc')


@pytest.fixture
def mock_get_temperature_adc(mocker):
    mock_get_temperature_adc = mocker.patch.object(module, '_get_temperature_adc')
    mock_get_temperature_adc.return_value = Mock(
        value=sentinel.digital_count,
        voltage=sentinel.voltage,
    )

    return mock_get_temperature_adc


class TestGetTemperatureAdc:
    def teardown(self):
        # Reset global variable between tests
        module._temperature_adc_channel = None

    def test_initilizes_on_first_call(self, mock_initialize_temperature_adc):
        assert module._temperature_adc_channel is None

        actual_temperature_adc_channel = module._get_temperature_adc()

        assert mock_initialize_temperature_adc.call_count == 1
        assert module._temperature_adc_channel is not None
        assert module._temperature_adc_channel == actual_temperature_adc_channel

    def test_does_not_initialize_on_second_call(self, mock_initialize_temperature_adc):
        assert module._temperature_adc_channel is None

        module._get_temperature_adc()
        actual_temperature_adc_channel = module._get_temperature_adc()

        assert mock_initialize_temperature_adc.call_count == 1
        assert module._temperature_adc_channel is not None
        assert module._temperature_adc_channel == actual_temperature_adc_channel


class TestReadTemperature:
    def test_returns_temperature_reading(self, mocker, mock_get_temperature_adc):
        mocker.patch.object(module, 'datetime', Mock(now=lambda: sentinel.datetime_now))

        actual = module.read_temperature()

        expected = module.TemperatureReading(
            capture_timestamp=sentinel.datetime_now,
            digital_count=sentinel.digital_count,
            voltage=sentinel.voltage
        )

        assert actual == expected


class TestReadTemperatures:
    def test_returns_n_temperature_readings(self, mocker, mock_get_temperature_adc):
        number_of_readings_to_collect = 10
        actual_readings = module._read_temperatures(number_of_readings_to_collect)

        assert len(actual_readings) == number_of_readings_to_collect

        unique_timestamps = {reading.capture_timestamp for reading in actual_readings}
        assert len(unique_timestamps) == number_of_readings_to_collect

    def test_records_actual_datetimes(self, mocker, mock_get_temperature_adc):
        number_of_readings_to_collect = 10
        actual_readings = module._read_temperatures(number_of_readings_to_collect)

        unique_timestamps = {reading.capture_timestamp for reading in actual_readings}
        assert len(unique_timestamps) == number_of_readings_to_collect


class TestGetOrCreateTemperatureLog:
    def test_does_not_create_or_update_file_if_exists(self, tmp_path):
        # tmp_path is a PosixPath instance. Python 3.5's os.path.join doesn't know how to handle it.
        mock_experiment_directory = str(tmp_path)
        mock_temperature_log_filename = 'temperature_log_filename'

        # Create a mock pre-existing log file with a mock header
        mock_log_filepath = os.path.join(mock_experiment_directory, mock_temperature_log_filename)

        mock_header = u'mock header'
        with open(mock_log_filepath, 'w') as f:
            f.write(mock_header)

        actual_log_filepath = module._get_or_create_temperature_log(
            experiment_directory=mock_experiment_directory,
            temperature_log_filename=mock_temperature_log_filename
        )

        with open(actual_log_filepath, 'r') as f:
            assert f.read() == mock_header

    def test_creates_file_with_header_if_not_exists(self, tmp_path):
        # tmp_path is a PosixPath instance. Python 3.5's os.path.join doesn't know how to handle it.
        mock_experiment_directory = str(tmp_path)
        mock_temperature_log_filename = 'temperature_log_filename'

        actual_log_filepath = module._get_or_create_temperature_log(
            experiment_directory=mock_experiment_directory,
            temperature_log_filename=mock_temperature_log_filename
        )
        expected_log_filepath = os.path.join(mock_experiment_directory, mock_temperature_log_filename)

        assert actual_log_filepath == expected_log_filepath
        with open(actual_log_filepath, 'r') as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == list(module.TemperatureReading._fields)


MOCK_DIGITAL_COUNT = 12345.0
MOCK_VOLTAGE = 0.12345


def _mock_read_temperature():
    return module.TemperatureReading(
        capture_timestamp=datetime.now(),
        digital_count=MOCK_DIGITAL_COUNT,
        voltage=MOCK_VOLTAGE
    )


@pytest.fixture
def mock_read_temperature(mocker):
    mock_read_temperature = mocker.patch.object(module, 'read_temperature')
    mock_read_temperature.side_effect = _mock_read_temperature

    return mock_read_temperature


def _get_log_readings(log_filepath):
    with open(log_filepath, 'r') as f:
        readings = list(csv.DictReader(f))

        return [dict(reading) for reading in readings]


class TestLogTemperature:
    def test_appends_temperature_reading_rows(self, tmp_path, mock_get_temperature_adc):
        number_of_readings_to_average = 1

        mock_get_temperature_adc.return_value = Mock(
            value=MOCK_DIGITAL_COUNT,
            voltage=MOCK_VOLTAGE,
        )

        mock_experiment_directory = str(tmp_path)  # Python 3.5 os.path.join can't handle tmp_path as PosixPath

        capture_time_1 = datetime(2019, 1, 1, 12, 13, 14)
        capture_time_2 = datetime(2019, 1, 2, 1, 2, 3)
        module.log_temperature(mock_experiment_directory, capture_time_1, number_of_readings_to_average)
        module.log_temperature(mock_experiment_directory, capture_time_2, number_of_readings_to_average)

        expected_log_filepath = os.path.join(
            mock_experiment_directory,
            module.TEMPERATURE_LOG_FILENAME
        )

        assert _get_log_readings(expected_log_filepath) == [
            {
                'capture_timestamp': '2019-01-01 12:13:14',
                'digital_count': str(MOCK_DIGITAL_COUNT),
                'voltage': str(MOCK_VOLTAGE),
            },
            {
                'capture_timestamp': '2019-01-02 01:02:03',
                'digital_count': str(MOCK_DIGITAL_COUNT),
                'voltage': str(MOCK_VOLTAGE),
            }
        ]

    def test_logs_averaged_reading_with_provided_capture_timestamp(self, tmp_path, mock_get_temperature_adc):
        number_of_readings_to_average = 10

        # Return multiple different readings so we can assert they are averaged
        mock_get_temperature_adc.side_effect = [
            Mock(
                value=i,
                voltage=i,
            )
            for i in range(number_of_readings_to_average)
        ]
        expected_average = 4.5

        mock_experiment_directory = str(tmp_path)  # Python 3.5 os.path.join can't handle tmp_path as PosixPath

        capture_time = datetime(2019, 1, 1, 12, 13, 14)
        module.log_temperature(
            experiment_directory=mock_experiment_directory,
            capture_time=capture_time,
            number_of_readings_to_average=number_of_readings_to_average
        )

        expected_log_filepath = os.path.join(
            mock_experiment_directory,
            module.TEMPERATURE_LOG_FILENAME
        )

        assert _get_log_readings(expected_log_filepath) == [
            {
                'capture_timestamp': '2019-01-01 12:13:14',
                'digital_count': str(expected_average),
                'voltage': str(expected_average),
            },
        ]

    def test_logs_unaveraged_readings(self, tmp_path, mock_get_temperature_adc):
        mock_get_temperature_adc.return_value = Mock(
            value=MOCK_DIGITAL_COUNT,
            voltage=MOCK_VOLTAGE,
        )

        mock_experiment_directory = str(tmp_path)  # Python 3.5 os.path.join can't handle tmp_path as PosixPath

        number_of_readings_to_average = 10
        module.log_temperature(
            experiment_directory=mock_experiment_directory,
            capture_time=datetime(2019, 1, 1, 12, 13, 14),
            number_of_readings_to_average=number_of_readings_to_average
        )

        expected_unaveraged_log_filepath = os.path.join(
            mock_experiment_directory,
            module.UNAVERAGED_TEMPERATURE_LOG_FILENAME
        )

        actual_readings = _get_log_readings(expected_unaveraged_log_filepath)

        unique_timestamps = {reading['capture_timestamp'] for reading in actual_readings}
        assert len(unique_timestamps) == number_of_readings_to_average
        assert len(actual_readings) == number_of_readings_to_average
