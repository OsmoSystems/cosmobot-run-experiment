#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='cosmobot_run_experiment',
    version='0.0.1',
    author='Osmo Systems',
    author_email='dev@osmobot.com',
    description='Script for running an image-collecting experiment on a Raspberry Pi',
    url='https://github.com/OsmoSystems/cosmobot-run-experiment.git',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['run_experiment = cosmobot_run_experiment.experiment:run_experiment']
    },
    install_requires=[],
    include_package_data=True
)
