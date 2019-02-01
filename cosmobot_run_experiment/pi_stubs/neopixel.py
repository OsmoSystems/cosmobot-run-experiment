class Pixel():
    def show(self):
        return True

    def fill(self, color):
        return True


class NeoPixel(object):
    def __init__(self, gpiopin, number_of_leds, brightness, pixel_order):
        self.gpiopin = gpiopin
        self.number_of_leds = number_of_leds
        self.brightness = brightness
        self.pixel_order = pixel_order
        self.pixels = [
            Pixel(), Pixel(), Pixel(), Pixel(),
            Pixel(), Pixel(), Pixel(), Pixel(),
            Pixel(), Pixel(), Pixel(), Pixel(),
            Pixel(), Pixel(), Pixel(), Pixel()
        ]

    def __getitem__(self, item):
        return self.pixels[item]

    def __setitem__(self, key, item):
        self.pixels[key] = item
