import csv
import os

try:
    from w1thermsensor import W1ThermSensor  # noqa: E0401  Unable to import
except ImportError:
    print("Unable to import pi specific modules to control leds")
    print("Using stubbed out board & neopixel modules instead")
    from .pi_stubs import w1thermsensor

sensor = W1ThermSensor()


def read_temperature():
    return sensor.get_temperature()


def create_temperature_log(experiment_directory):
    headers = ['filename', 'temperature_before_capture', 'temperature_after_capture']
    temperature_log_filepath = os.path.join(experiment_directory, 'temperature.csv')

    with open(temperature_log_filepath, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(headers)


def log_temperature(experiment_directory, image_filename, temperature_before_capture, temperature_after_capture):
    temperature_log_filepath = os.path.join(experiment_directory, 'temperature.csv')

    with open(temperature_log_filepath, 'a') as file:
        writer = csv.writer(file)
        writer.writerow([image_filename, temperature_before_capture, temperature_after_capture])


# def steinhart_temperature_in_celcius(r, Ro=10000.0, To=25.0, beta=3950.0):
#     steinhart = math.log(r / Ro) / beta      # log(R/Ro) / beta
#     steinhart += 1.0 / (To + 273.15)         # log(R/Ro) / beta + 1/To
#     steinhart = (1.0 / steinhart) - 273.15   # Invert, convert to C
#     return steinhart
#
#
# def temperature_from_thermistor(ADC_value):
#     resistance = 10000 / (65535 / ADC_value - 1)
#     return steinhart_temperature_in_celcius(resistance)
#
#
# def temperature():
#     thermistor = analogio.AnalogIn(board.A1)
#     return thermistor.value
