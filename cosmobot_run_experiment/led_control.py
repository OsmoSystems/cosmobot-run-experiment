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


DIGITAL_LED_PIN_ON_HIGH = board.D5
DIGITAL_LED_PIN_ON_LOW = board.D6


def _control_led(led_on, pin, pin_high):
    logging.info(
        "Turning LED {led_setpoint} (DIO pin {pin} -> {pin_setpoint})".format(
            led_setpoint="on" if led_on else "off",
            pin=pin,
            pin_setpoint="high" if pin_high else "low",
        )
    )

    led_pin = digitalio.DigitalInOut(pin=pin)
    led_pin.direction = digitalio.Direction.OUTPUT
    led_pin.value = pin_high


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
    _control_led(led_on, pin=DIGITAL_LED_PIN_ON_HIGH, pin_high=led_on)
    _control_led(led_on, pin=DIGITAL_LED_PIN_ON_LOW, pin_high=not led_on)


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
