'''
Stubbed out DigitalIO module to support software development
on a non raspberry pi - The digitalio module can not be installed on a
development machine and this stubbed out module simulates the functionality
we use on a pi.
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
