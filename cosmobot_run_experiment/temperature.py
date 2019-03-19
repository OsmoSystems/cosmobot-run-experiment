import csv
import os

try:
    from w1thermsensor import W1ThermSensor  # noqa: E0401  Unable to import
except ImportError:
    print("Unable to import pi specific modules to control leds")
    print("Using stubbed out board & neopixel modules instead")
    from .pi_stubs.w1thermsensor import W1ThermSensor

sensor = W1ThermSensor()


def read_temperature():
    return sensor.get_temperature()


def create_temperature_log(experiment_directory):
    headers = ['filename', 'temperature_before_capture', 'temperature_after_capture']
    temperature_log_filepath = os.path.join(experiment_directory, 'temperature.csv')

    with open(temperature_log_filepath, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(headers)


def log_temperature_at_capture(experiment_directory, image_filename, temperature_before_capture, temperature_after_capture):
    temperature_log_filepath = os.path.join(experiment_directory, 'temperature.csv')

    with open(temperature_log_filepath, 'a') as file:
        writer = csv.writer(file)
        writer.writerow([image_filename, temperature_before_capture, temperature_after_capture])
