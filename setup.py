#!/usr/bin/env python
from setuptools import setup, find_packages

# Raspberry Pi's "platform machine" is 'armv7l', which should broadly distinguish it from dev machines
RASPBERRY_PI_ONLY_FILTER = ';platform_machine==armv7l'

setup(
    name='cosmobot_run_experiment',
    version='0.0.1',
    author='Osmo Systems',
    author_email='dev@osmobot.com',
    description='Script for running an image-collecting experiment on a Raspberry Pi',
    url='https://github.com/OsmoSystems/cosmobot-run-experiment.git',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'run_experiment = cosmobot_run_experiment.experiment:run_experiment',
            'review_exposure = cosmobot_run_experiment.exposure:review_exposure',
            'set_led = cosmobot_run_experiment.led_control:set_led',
        ]
    },
    install_requires=[
        # These deps should install on any system
        'numpy',
        'picamraw',
        'psutil',
        'pyyaml',
    ],
    extras_require={
        # These deps are only relevant on a raspberry pi (I/O stuff)
        # To install editable (local): pip install -e .[io]
        'io': [
            'adafruit-blinka',
            'adafruit-circuitpython-ads1x15',
            'adafruit-circuitpython-neopixel',
            'rpi_ws281x',
            'RPI.GPIO',
        ]
    },
    include_package_data=True
)
