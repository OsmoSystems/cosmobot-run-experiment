'''
Stubbed out NeoPixel and Pixel classes to support software development
on a non raspberry pi as neopixel module can not be installed on a development
machine.

See led.py for methods that are currently stubbed and
https://circuitpython.readthedocs.io/projects/neopixel/en/latest/ for latest NeoPixel
code.
'''

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
