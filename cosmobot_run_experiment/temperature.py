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


# DS18B20-1 Calibration (0308977944a1)
#calibration_min = (10.0, 7.25617) # 2.74383
#calibration_mid = (22.5, 19.73299) # 2.76701
#calibration_max = (35.0, 32.13926) # 2.86074

# DS18B20-2 Calibration (030897796419)
calibration_min = (10.0, 8.91158)
calibration_mid = (22.5, 21.17151)
calibration_max = (35.0, 33.27658)

def adjust_temperature(in_temperature):
    min_calibration_point_water_bath = calibration_min[0]
    min_calibration_point_sensor = calibration_min[1]

    mid_calibration_point_water_bath = calibration_mid[0]
    mid_calibration_point_sensor = calibration_mid[1]

    max_calibration_point_water_bath = calibration_max[0]
    max_calibration_point_sensor = calibration_max[1]

    min_sensor_point_to_use = min_calibration_point_sensor
    max_sensor_point_to_use = mid_calibration_point_sensor
    min_water_bath_point_to_use = min_calibration_point_water_bath
    max_water_bath_point_to_use = mid_calibration_point_water_bath

    if in_temperature > mid_calibration_point_sensor:
        min_sensor_point_to_use = mid_calibration_point_sensor
        max_sensor_point_to_use = max_calibration_point_sensor
        min_water_bath_point_to_use = mid_calibration_point_water_bath
        max_water_bath_point_to_use = max_calibration_point_water_bath

    range_sensor = max_sensor_point_to_use - min_sensor_point_to_use
    diff_from_min_sensor = in_temperature - min_sensor_point_to_use
    range_water_bath = max_water_bath_point_to_use - min_water_bath_point_to_use

    percentage_of_range_sensor = diff_from_min_sensor / range_sensor

    calibrated_temperature = min_water_bath_point_to_use + (range_water_bath * percentage_of_range_sensor)
    return calibrated_temperature
