import math

try:
    import board  # noqa: E0401  Unable to import
    import analogio  # noqa: E0401  Unable to import
except ImportError:
    print("Unable to import pi specific modules to control leds")
    print("Using stubbed out board & neopixel modules instead")
    from .pi_stubs import board, analogio


def steinhart_temperature_in_celcius(r, Ro=10000.0, To=25.0, beta=3950.0):
    steinhart = math.log(r / Ro) / beta      # log(R/Ro) / beta
    steinhart += 1.0 / (To + 273.15)         # log(R/Ro) / beta + 1/To
    steinhart = (1.0 / steinhart) - 273.15   # Invert, convert to C
    return steinhart


def temperature_from_thermistor(ADC_value):
    resistance = 10000 / (65535 / ADC_value - 1)
    return steinhart_temperature_in_celcius(resistance)


def temperature():
    thermistor = analogio.AnalogIn(board.A1)
    return thermistor.value
