from collections import namedtuple
import csv
from datetime import datetime
import logging
import os
import platform

import numpy as np

# Support development without needing pi specific modules installed.
if platform.machine() == 'armv7l':
    from adafruit_ads1x15 import ads1115, analog_in
    import board
    import busio
else:
    logging.warning('Using library stubs for non-raspberry-pi machine')
    from cosmobot_run_experiment.pi_stubs import board, busio
    from cosmobot_run_experiment.pi_stubs.adafruit_ads1x15 import ads1115, analog_in


TEMPERATURE_LOG_FILENAME = 'temperature.csv'
UNAVERAGED_TEMPERATURE_LOG_FILENAME = 'unaveraged_temperature.csv'


# In the past, we've seen issues with opening the same I/O channels with multiple objects
# Use a global variable for the temperature ADC object so that it is only initialized once
_temperature_adc_channel = None


def _initialize_temperature_adc():
    # Initialize the I2C bus and the ADC (ADS1115)
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ads1115.ADS1115(i2c)

    # Our thermistor is set up single-ended on the P0 channel of the ADC
    return analog_in.AnalogIn(ads, ads1115.P0)


def _get_temperature_adc():
    global _temperature_adc_channel

    if _temperature_adc_channel is None:
        _temperature_adc_channel = _initialize_temperature_adc()

    return _temperature_adc_channel


TemperatureReading = namedtuple('TemperatureReading', [
    'capture_timestamp',
    'digital_count',
    'voltage'
])


def read_temperature():
    ''' Collects a temperature measurement from the ADC channel (on the I2C bus)

    Returns:
        A TemperatureReading
    '''
    temperature_adc_channel = _get_temperature_adc()

    return TemperatureReading(
        capture_timestamp=datetime.now(),
        digital_count=temperature_adc_channel.value,
        voltage=temperature_adc_channel.voltage
    )


def _read_temperatures(number_of_readings_to_collect):
    return [
        read_temperature()
        for i in range(number_of_readings_to_collect)
    ]


def _get_or_create_temperature_log(experiment_directory, temperature_log_filename):
    temperature_log_filepath = os.path.join(experiment_directory, temperature_log_filename)

    log_file_exists = os.path.isfile(temperature_log_filepath)

    if not log_file_exists:
        with open(temperature_log_filepath, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=TemperatureReading._fields)
            writer.writeheader()

    return temperature_log_filepath


def _log_temperature(experiment_directory, temperature_log_filename, temperature_readings):
    temperature_log_filepath = _get_or_create_temperature_log(experiment_directory, temperature_log_filename)

    with open(temperature_log_filepath, 'a') as f:
        writer = csv.DictWriter(f, fieldnames=TemperatureReading._fields)

        for temperature_reading in temperature_readings:
            writer.writerow(temperature_reading._asdict())

    return temperature_log_filepath


def log_temperature(experiment_directory, capture_time, number_of_readings_to_average):
    ''' Collects multiple temperature readings, and logs the average to one file and all of the raw readings to a
        separate file. The averaged reading gets logged with the provided capture_time, but the raw readings get
        logged with the actual datetimes they were recorded

    Args:
        experiment_directory: The full path of the directory where the logs will be created
        capture_time: A datetime which will be used in the averaged temperature log
        number_of_readings_to_average: The number of readings to collect and average over

    Returns:
        None, but has the side-effect of creating and/or updating two csv logs
    '''
    temperature_readings = _read_temperatures(number_of_readings_to_average)

    averaged_reading = TemperatureReading(
        capture_timestamp=capture_time,
        digital_count=np.average([reading.digital_count for reading in temperature_readings]),
        voltage=np.average([reading.voltage for reading in temperature_readings])
    )

    _log_temperature(experiment_directory, UNAVERAGED_TEMPERATURE_LOG_FILENAME, temperature_readings)
    _log_temperature(experiment_directory, TEMPERATURE_LOG_FILENAME, [averaged_reading])
