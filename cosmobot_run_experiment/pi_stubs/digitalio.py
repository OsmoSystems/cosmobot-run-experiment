'''
Stubbed out DigitalIO module
'''
from enum import Enum


class Direction(Enum):
    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'


class DigitalInOut(object):
    def __init__(self, pin):
        self.pin = pin
        self.value = False
        self.direction = None
