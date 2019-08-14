import argparse
import logging
import platform
import sys

# Support development without needing pi specific modules installed.
from time import sleep

if platform.machine() == "armv7l":
    import board  # noqa: E0401  Unable to import
    import digitalio  # noqa: E0401  Unable to import
else:
    logging.warning("Using library stubs for non-raspberry-pi machine")
    from cosmobot_run_experiment.pi_stubs import board, digitalio


DIGITAL_LED_PIN = board.D6


def control_led(led_on=True):
    """ turn on/off Digital IO LED
    Note that the LED is connected through a relay such that setting the DIO pin *low* will turn the LED *on*,
    and vice versa.

    Args:
        led_on: boolean; if True, turn LED on by setting the DIO pin low. if False, turn off LED by setting DIO pin high
    Returns:
        None
    """
    pin_setpoint = not led_on
    logging.info(
        "Turning LED {led_setpoint} (DIO pin {pin} -> {pin_setpoint})".format(
            led_setpoint="on" if led_on else "off",
            pin=DIGITAL_LED_PIN,
            pin_setpoint="high" if pin_setpoint else "low",
        )
    )

    led_pin = digitalio.DigitalInOut(pin=DIGITAL_LED_PIN)
    led_pin.direction = digitalio.Direction.OUTPUT
    led_pin.value = pin_setpoint


def set_led_cli(cli_args=None):
    """ Turn on or off the LED based on command-line parameters
     Args:
        args: list of command-line-like argument strings such as sys.argv. if not provided, sys.argv[1:] will be used
     Returns:
        None
    """

    if cli_args is None:
        # First argument is the name of the command itself, not an "argument" we want to parse
        cli_args = sys.argv[1:]

    arg_parser = argparse.ArgumentParser(
        description="Turn on or off LED on digital pin {}".format(DIGITAL_LED_PIN)
    )

    arg_parser.add_argument(
        "state",
        choices=["on", "off"],
        help='LED state to set: "on" to turn LED on; "off" to turn it off.',
    )

    args = arg_parser.parse_args(cli_args)

    control_led(led_on=args.state == "on")


def flash_led_once(wait_time_s, on_time_s):
    """ Wait a predetermined amount of time and then turn the LED on for a predetermined amount of time

    Args:
        wait_time_s: amount of time (s) to wait before turning the LED on
        on_time_s: amount of time (s) to leave the LED on

    Returns: None

    """
    sleep(wait_time_s)
    control_led(True)
    sleep(on_time_s)
    control_led(False)


def flash_led_cli(cli_args=None):
    """ flash the LED continuously based on command-line parameters
     Args:
        args: list of command-line-like argument strings such as sys.argv. if not provided, sys.argv[1:] will be used
     Returns:
        None
    """

    logging_format = "%(asctime)s [%(levelname)s]--- %(message)s"
    logging.basicConfig(
        level=logging.INFO, format=logging_format, handlers=[logging.StreamHandler()]
    )

    if cli_args is None:
        # First argument is the name of the command itself, not an "argument" we want to parse
        cli_args = sys.argv[1:]

    arg_parser = argparse.ArgumentParser(
        description="Flash LED on digital pin {}".format(DIGITAL_LED_PIN)
    )

    arg_parser.add_argument(
        "on_time", type=float, help="Amount of time (s) to leave the LED on"
    )

    arg_parser.add_argument(
        "--wait_time",
        type=float,
        default=1,
        help="Amount of time (s) to wait before turning the LED on and between flashes",
    )

    args = arg_parser.parse_args(cli_args)

    while True:
        flash_led_once(wait_time_s=args.wait_time, on_time_s=args.on_time)
