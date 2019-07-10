import argparse
import logging
import platform
import sys

# Support development without needing pi specific modules installed.
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
    logging.info("Turning LED {}".format("on" if led_on else "off"))

    led = digitalio.DigitalInOut(pin=DIGITAL_LED_PIN)
    led.direction = digitalio.Direction.OUTPUT
    led.value = not led_on


def main(cli_args=None):
    """ Control LEDs based on command-line parameters
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
