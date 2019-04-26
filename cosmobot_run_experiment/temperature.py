from collections import namedtuple
import csv
import os
import platform

# Support development without needing pi specific modules installed.
if platform.machine() == 'armv7l':
    from adafruit_ads1x15 import ads1115, analog_in
    import board
    import busio
else:
    print('Using library stubs for non-raspberry-pi machine')
    from cosmobot_run_experiment.pi_stubs import board, busio
    from cosmobot_run_experiment.pi_stubs.adafruit_ads1x15 import ads1115, analog_in


TEMPERATURE_LOG_FILENAME = 'temperature.csv'

# Initialize the I2C bus and the ADC (ADS1115)
i2c = busio.I2C(board.SCL, board.SDA)
ads = ads1115.ADS1115(i2c)

# Our thermister is set up singled-ended on the P0 channel of the ADC
temperature_adc_channel = analog_in.AnalogIn(ads, ads1115.P0)


TemperatureReading = namedtuple('TemperatureReading', [
    'capture_timestamp',
    'raw_temperature_value',
    'raw_temperature_voltage'
])


def read_temperature(capture_timestamp):
    global temperature_adc_channel

    return TemperatureReading(
        capture_timestamp=capture_timestamp,
        raw_temperature_value=temperature_adc_channel.value,
        raw_temperature_voltage=temperature_adc_channel.voltage
    )


def _get_or_create_temperature_log(experiment_directory):
    temperature_log_filepath = os.path.join(experiment_directory, TEMPERATURE_LOG_FILENAME)
    log_file_exists = os.path.isfile(temperature_log_filepath)

    if not log_file_exists:
        with open(temperature_log_filepath, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=TemperatureReading._fields)
            writer.writeheader()

    return temperature_log_filepath


def log_temperature(experiment_directory, capture_time):
    temperature_log_filepath = _get_or_create_temperature_log(experiment_directory)

    temperature_reading = read_temperature(capture_time)

    with open(temperature_log_filepath, 'a') as f:
        writer = csv.DictWriter(f, fieldnames=TemperatureReading._fields)
        writer.writerow(temperature_reading._asdict())

    return temperature_log_filepath
