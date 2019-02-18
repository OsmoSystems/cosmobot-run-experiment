'''
Stubbed out NeoPixel and Pixel module to support software development
on a non raspberry pi - The neopixel module can not be installed on a
development machine and this stubbed out module simulates the functionality
we use on a pi.

See led.py for methods that are currently stubbed and
https://circuitpython.readthedocs.io/projects/neopixel/en/latest/ for latest NeoPixel
code.
'''

GRB = (1, 0, 2)


class NeoPixel(object):
    def __init__(self, gpiopin, number_of_leds, brightness, pixel_order):
        self.gpiopin = gpiopin
        self.number_of_leds = number_of_leds
        self.brightness = brightness
        self.pixel_order = pixel_order
        self.pixels = [None for i in range(number_of_leds)]

    def __getitem__(self, item):
        return self.pixels[item]

    def __setitem__(self, key, item):
        self.pixels[key] = item
