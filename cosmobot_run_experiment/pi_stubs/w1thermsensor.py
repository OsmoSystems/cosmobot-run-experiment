from random import uniform

class W1ThermSensor(object):
    def get_temperature(self):
        return 20.0 + uniform(0, 5)
