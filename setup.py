#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='osmo_camera',
    version='0.0.1',
    author='Osmo Systems',
    author_email='dev@osmobot.com',
    description='Prototype code for an osmobot camera sensor',
    url='https://www.github.com/osmosystems/camera-sensor-prototype',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['run_experiment = osmo_camera.experiment:run_experiment']
    },
    install_requires=[],
    include_package_data=True
)
