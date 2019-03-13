class AnalogIn(object):
    def __init__(self, gpiopin):
        self.gpiopin = gpiopin
        self.value = 10000
