import argparse
import logging
import sys

#  Import pattern to support development without needing pi specific modules installed.
#  board module has been stubbed out within "pi_stubs" folder
try:
    import board  # noqa: E0401  Unable to import
    import digitalio  # noqa: E0401  Unable to import
except ImportError:
    print('''
        Unable to import pi specific modules to control leds
        Using stubbed out modules instead
    ''')
    from cosmobot_run_experiment.pi_stubs import board, digitalio


DIGITAL_LED_PIN = board.D6


def control_led(on=True):
    ''' turn on/off Digital IO LED

    Args:
        on: boolean; if True, turn LED on. if False, turn off
    Returns:
        None
    '''
    logging.info('Turning LED {}'.format('on' if on else 'off'))

    led = digitalio.DigitalInOut(pin=DIGITAL_LED_PIN)
    led.direction = digitalio.Direction.OUTPUT
    led.value = on


def main(cli_args=None):
    ''' Control LEDs based on command-line parameters
     Args:
        args: list of command-line-like argument strings such as sys.argv. if not provided, sys.argv[1:] will be used
     Returns:
        None
    '''

    if cli_args is None:
        # First argument is the name of the command itself, not an "argument" we want to parse
        cli_args = sys.argv[1:]

    arg_parser = argparse.ArgumentParser(description='Turn on or off LED on digital pin {}'.format(DIGITAL_LED_PIN))

    arg_parser.add_argument(
        '--on',
        action='store_true',
        help='If provided, turn LED on (otherwise, turn it off)',
    )

    args = arg_parser.parse_args(cli_args)

    control_led(on=args.on)
