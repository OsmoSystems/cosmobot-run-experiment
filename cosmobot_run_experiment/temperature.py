from collections import namedtuple
from datetime import datetime
import csv
import os

try:
    from adafruit_ads1x15 import ads1115, analog_in
    import board
    import busio
except ImportError:
    print('''
        Unable to import pi specific modules to control leds
        Using stubbed out board & neopixel modules instead
    ''')
    pass  # TODO: implement stubs


# Initialize the I2C bus and the ADC (ADS1115)
i2c = busio.I2C(board.SCL, board.SDA)
ads = ads1115.ADS1115(i2c)

# Our thermister is set up singled-ended on the P0 channel of the ADC
channel = analog_in.AnalogIn(ads, ads1115.P0)


TemperatureReading = namedtuple('TemperatureReading', ['image_filename', 'timestamp', 'raw_temperature_value', 'raw_temperature_voltage'])


def log_temperature(experiment_directory, image_filename):
    temperature_log_filepath = os.path.join(experiment_directory, 'temperature.csv')
    log_file_exists = os.path.isfile(temperature_log_filepath)

    temperature_reading = TemperatureReading(
        image_filename=image_filename,
        timestamp=datetime.now(),
        raw_temperature_value=channel.value,
        raw_temperature_voltage=channel.voltage
    )

    with open(temperature_log_filepath, 'a') as f:
        writer = csv.DictWriter(f, fieldnames=TemperatureReading._fields)

        if not log_file_exists:
            writer.writeheader()

        writer.writerow(temperature_reading._asdict())

    return temperature_log_filepath


# TODO: remove
if __name__ == '__main__':
    temperature_log_filepath = log_temperature(experiment_directory='.', image_filename='img.jpg')
    print(temperature_log_filepath)
