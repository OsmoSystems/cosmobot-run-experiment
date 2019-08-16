import argparse
import logging
import platform
import sys
from time import sleep

# Support development without needing pi specific modules installed.
if platform.machine() == "armv7l":
    import board  # noqa: E0401  Unable to import
    import digitalio  # noqa: E0401  Unable to import
else:
    logging.warning("Using library stubs for non-raspberry-pi machine")
    from cosmobot_run_experiment.pi_stubs import board, digitalio


DIGITAL_LED_PIN_ON_HIGH = board.D5
DIGITAL_LED_PIN_ON_LOW = board.D6


def _set_dio_pin(pin, value: bool):
    logging.info(
        "Setting DIO pin {pin} -> {pin_setpoint}".format(
            pin=pin, pin_setpoint="high" if value else "low"
        )
    )

    dio_pin = digitalio.DigitalInOut(pin=pin)
    dio_pin.direction = digitalio.Direction.OUTPUT
    dio_pin.value = value


def control_led(led_on=True):
    """ turn on/off Digital IO LED

    This function is intended to be used to turn an LED on and off.

    However, it is implemented to actually control _two_ pins, in opposite directions.

    This allows us to choose whether we are controlling the LED through a device which
    turns the LED *on* when the pin is *high*, or *on* when the pin is *low*, simply by
    connecting to the appropriate pin:

        D5: LED *on* when the pin is *high*
        D6: LED *on* when the pin is *low*

    Args:
        led_on: boolean; if True, turn LED on. if False, turn LED off
    Returns:
        None
    """
    logging.info(
        "Turning LED {led_setpoint}".format(led_setpoint="on" if led_on else "off")
    )
    _set_dio_pin(pin=DIGITAL_LED_PIN_ON_HIGH, value=led_on)
    _set_dio_pin(pin=DIGITAL_LED_PIN_ON_LOW, value=not led_on)


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
        description="Turn on or off LED on digital pin {} (if pin high = led on) or {} (if pin low = led on)".format(
            DIGITAL_LED_PIN_ON_HIGH, DIGITAL_LED_PIN_ON_LOW
        )
    )

    arg_parser.add_argument(
        "state",
        choices=["on", "off"],
        help='LED state to set: "on" to turn LED on; "off" to turn it off.',
    )

    args = arg_parser.parse_args(cli_args)

    control_led(led_on=args.state == "on")


def flash_led_once(wait_time_seconds, on_time_seconds):
    """ Wait a predetermined amount of time and then turn the LED on for a predetermined amount of time

    Args:
        wait_time_seconds: amount of time (s) to wait before turning the LED on
        on_time_seconds: amount of time (s) to leave the LED on

    Returns: None

    """
    sleep(wait_time_seconds)
    control_led(True)
    sleep(on_time_seconds)
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
        description=(
            "Flash LED on/off indefinitely on digital pin "
            "{} (if pin high = led on) or {} (if pin low = led on) (kill with ctrl+c)"
        ).format(DIGITAL_LED_PIN_ON_HIGH, DIGITAL_LED_PIN_ON_LOW)
    )

    arg_parser.add_argument(
        "on_time",
        type=float,
        help="Amount of time (s) to leave the LED on during a single flash",
    )

    arg_parser.add_argument(
        "--wait_time",
        type=float,
        default=1,
        help="Amount of time (s) to wait before turning the LED on and between flashes",
    )

    args = arg_parser.parse_args(cli_args)

    while True:
        flash_led_once(wait_time_seconds=args.wait_time, on_time_seconds=args.on_time)
