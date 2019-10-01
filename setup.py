#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
    name="cosmobot_run_experiment",
    version="0.0.1",
    author="Osmo Systems",
    author_email="dev@osmobot.com",
    description="Script for running an image-collecting experiment on a Raspberry Pi",
    url="https://github.com/OsmoSystems/cosmobot-run-experiment.git",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "run_experiment = cosmobot_run_experiment.experiment:run_experiment",
            "review_exposure = cosmobot_run_experiment.exposure:review_exposure",
            "set_led = cosmobot_run_experiment.led_control:set_led_cli",
            "flash_led = cosmobot_run_experiment.led_control:flash_led_cli",
        ]
    },
    install_requires=[
        # These deps should install on any system
        "boto",
        "numpy",
        "picamraw",
        "psutil",
        "pyyaml",
    ],
    extras_require={
        # These deps are only relevant on a raspberry pi (I/O stuff)
        # To install editable (local): pip install -e .[io]
        # fmt: off
        "io": [
            "RPI.GPIO",
        ]
        # fmt: on
    },
    include_package_data=True,
)
