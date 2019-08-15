import argparse
import sys
import os
from collections import namedtuple
from datetime import datetime, timedelta
from socket import gethostname
from subprocess import check_output, CalledProcessError
from textwrap import dedent
from uuid import getnode as get_mac

import yaml

from .file_structure import iso_datetime_for_filename, get_base_output_path

DEFAULT_ISO = 100
DEFAULT_EXPOSURE = 1.5
DEFAULT_CAPTURE_PARAMS = " -ISO {DEFAULT_ISO}".format(**locals())

ExperimentConfiguration = namedtuple(
    "ExperimentConfiguration",
    [
        "name",  # The Name of the experiment.  Used for naming directories for output.
        "interval",  # The interval in seconds between the capture of images.
        "duration",  # How long in seconds should the experiment run for.
        "variants",  # array of ExperimentVariants that define different capture settings to be run each iteration
        "start_date",  # date the experiment was started
        "end_date",  # date at which to end the experiment.  If duration is not set then this is effectively indefinite
        "experiment_directory_path",  # directory/path to write files to
        "command",  # full command with arguments issued to start the experiment from the command line
        "git_hash",  # git hash of camera-sensor-prototype repo
        "hostname",  # hostname of the device the experient was executed on
        "mac",  # mac address
        "skip_temperature",  # whether to skip recording temperature
        "skip_sync",  # whether to skip syncing to s3
        "erase_synced_files",  # whether to erase the local experiment folder after synced to s3
        "review_exposure",  # review exposure statistics after experiment finishes and do not sync to s3)
    ],
)

ExperimentVariant = namedtuple(
    "ExperimentVariant",
    [
        "capture_params",  # parameters to pass to raspistill binary through the command line
        "exposure_time",  # Length of camera exposure, us
        "camera_warm_up",  # Amount of time to let the camera warm up before taking an image, seconds
        "led_on",  # Whether LED should be on or off
        "led_warm_up",  # amount of time to wait for led to warm up before the camera takes its exposure
    ],
)


def _parse_args(args):
    """Extract and verify arguments passed in from the command line
     Args:
        args: list of command-line-like argument strings such as sys.argv
     Returns:
        dictionary of arguments parsed from the command line
    """
    arg_parser = argparse.ArgumentParser(
        description=dedent(
            """\
        Run an experiment, collecting images and setting LEDs at desired intervals.

        The --variant flag can be used to take images with multiple sets of specified camera and LED settings.
        """
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    arg_parser.add_argument(
        "--name", required=True, type=str, help="name for experiment"
    )
    arg_parser.add_argument(
        "--interval",
        required=True,
        type=float,
        help="interval between image capture in seconds",
    )
    arg_parser.add_argument(
        "--duration",
        required=False,
        type=float,
        default=None,
        help="Duration in seconds. Optional: if not provided, will run indefinitely.",
    )
    arg_parser.add_argument(
        "--variant",
        required=False,
        type=str,
        default=[],
        action="append",
        help=_get_variant_parser().format_help(),
    )

    arg_parser.add_argument(
        "--exposures",
        required=False,
        type=int,
        nargs="+",
        default=None,
        help='List of exposures to iterate capture through ex. "--exposures 0.1, 1"',
    )
    arg_parser.add_argument(
        "--isos",
        required=False,
        type=int,
        nargs="+",
        default=None,
        help='List of isos to iterate capture through ex. "--isos 100 200"\n'
        "If not provided and --exposures is provided, ISO {DEFAULT_ISO} "
        "will be used when iterating over exposures.".format(**globals()),
    )
    arg_parser.add_argument(
        "--skip-temperature",
        action="store_true",
        help="If provided, skips recording temperature.",
    )

    arg_parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="If provided, skips syncing files to s3.",
    )

    arg_parser.add_argument(
        "--erase-synced-files",
        action="store_true",
        help="If provided, uses s3 mv to erase files after sync is completed.",
    )

    arg_parser.add_argument(
        "--review-exposure",
        action="store_true",
        help="optionally review exposure at the end of the experiment",
    )

    # There could be arguments passed in that we want to ignore (e.g. led color, intensity)
    # parse_known_args and arg namespace is used to only utilize args that we care about in the prepare module.
    experiment_arg_namespace, _ = arg_parser.parse_known_args(args)
    return vars(experiment_arg_namespace)


def _get_variant_parser():
    """ Get the argparse.ArgumentParser instance used to parse LED variants out of a --variant command-line parameter
    """
    # Set this up so that _get_variant_parser().format_help() can be (roughly) used to describe
    arg_parser = argparse.ArgumentParser(
        # Hack: use "prog" for the whole intro since the .format_help() formatter places this nicely up front
        # with the LED param details afterwards
        prog=dedent(
            """
            --variant "VARIANT_PARAMS".
                VARIANT_PARAMS describes a variant of camera and LED parameters to use during experiment.
                Example:
                    --variant " -ISO 100 --exposure_time 0.5 --camera-warm-up 1 --led-on --led-warm-up 3"
                If multiple --variant parameters are provided, each variant will be used once per interval.

            Camera control:
                raspistill camera parameters within each --variant flag are passed directly to raspistill.
                Some relevant parameters:
                    "-ISO" should be a value from 100-800, in increments of 100
                    "--exposure_time" is in microseconds, and is undefined above 6s (--exposure_time 6)
                Ex: --variant "-ISO 100 --exposure_time 0.5 " --variant "-ISO 200 --exposure_time 0.1".
                Default: "{DEFAULT_CAPTURE_PARAMS}".

            LED control:
            """.format(
                **globals()
            )
        )
    )

    arg_parser.add_argument(
        "--exposure-time",
        required=False,
        type=float,
        default=DEFAULT_EXPOSURE,
        help="Exposure time for the image to be taken, in seconds. Default: 1.5s",
    )
    arg_parser.add_argument(
        "--camera-warm-up",
        required=False,
        type=float,
        default=5,
        help="Time to allow the camera sensor to warm up before exposure, in seconds. Default: 5s. Minimum: 1ms",
    )
    arg_parser.add_argument(
        "--led-on",
        action="store_true",
        help="If set, LED will be turned on for this variant",
    )
    arg_parser.add_argument(
        "--led-warm-up",
        required=False,
        type=float,
        default=0.8,
        help="If set, LED is turned on before initiating capture for a time value in seconds. Default: 0.8s",
    )
    return arg_parser


def _parse_variant(variant):
    parsed_args, remaining_args_for_capture = _get_variant_parser().parse_known_args(
        variant.split()
    )

    # capture_params aren't parsed as regular args - they'll just be passed wholesale into raspistill
    capture_params = " ".join(remaining_args_for_capture) or DEFAULT_CAPTURE_PARAMS

    if parsed_args.camera_warm_up < parsed_args.led_warm_up:
        raise ValueError(
            "LED warm up {} longer than camera warm up {} is not supported".format(
                parsed_args.led_warm_up, parsed_args.camera_warm_up
            )
        )

    return ExperimentVariant(
        capture_params=capture_params,
        exposure_time=parsed_args.exposure_time,
        camera_warm_up=parsed_args.camera_warm_up,
        led_on=parsed_args.led_on,
        led_warm_up=parsed_args.led_warm_up,
    )


def get_experiment_variants(args):
    variants = [_parse_variant(variant) for variant in args["variant"]]

    # add variants of exposure and iso lists if provided
    if args["exposures"]:
        isos = args["isos"] or [DEFAULT_ISO]
        variants.extend(
            _parse_variant(" --exposure-time {exposure} -ISO {iso}".format(**locals()))
            for exposure in args["exposures"]
            for iso in isos
        )

    if not variants:
        variants = [_parse_variant(DEFAULT_CAPTURE_PARAMS)]

    return variants


def _get_mac_address():
    integer_mac_address = get_mac()  # Returns as an integer
    hex_mac_address = hex(integer_mac_address).upper()
    return hex_mac_address[2:]  # Hex is in form '0X<mac address' - trim the '0X'


def _get_mac_last_4():
    return _get_mac_address()[-4:]


def get_experiment_configuration(cli_args):
    """Return a constructed named experimental configuration in a namedtuple.
     Args:
        cli_args: list of command-line argument strings like sys.argv
     Returns:
        an instance of ExperimentConfiguration namedtuple

    """
    args = _parse_args(cli_args)

    duration = args["duration"]
    start_date = datetime.now()
    end_date = (
        start_date if duration is None else start_date + timedelta(seconds=duration)
    )
    mac_address = _get_mac_address()
    mac_last_4 = _get_mac_last_4()

    iso_ish_datetime = iso_datetime_for_filename(start_date)
    name = args["name"]
    experiment_directory_name = "{iso_ish_datetime}-Pi{mac_last_4}-{name}".format(
        **locals()
    )
    experiment_directory_path = os.path.join(
        get_base_output_path(), experiment_directory_name
    )

    variants = get_experiment_variants(args)

    experiment_configuration = ExperimentConfiguration(
        name=args["name"],
        interval=args["interval"],
        duration=duration,
        start_date=start_date,
        end_date=end_date,
        experiment_directory_path=experiment_directory_path,
        command=" ".join(sys.argv),
        git_hash=_git_hash(),
        hostname=gethostname(),
        mac=mac_address,
        variants=variants,
        skip_temperature=args["skip_temperature"],
        skip_sync=args["skip_sync"],
        erase_synced_files=args["erase_synced_files"],
        review_exposure=args["review_exposure"],
    )

    return experiment_configuration


def create_file_structure_for_experiment(configuration):
    print(
        "Output directory is {configuration.experiment_directory_path}".format(
            **locals()
        )
    )
    os.makedirs(configuration.experiment_directory_path, exist_ok=True)

    metadata_path = os.path.join(
        configuration.experiment_directory_path, "experiment_metadata.yml"
    )
    with open(metadata_path, "w") as metadata_file:
        yaml.dump(configuration._asdict(), metadata_file, default_flow_style=False)


def hostname_is_correct(hostname):
    """Does hostname follow the pattern we expect pi-cam-[last four of MAC]
     Args:
        hostname: hostname of machine
     Returns:
        Boolean: is hostname valid
    """
    mac_last_4 = _get_mac_last_4()
    return hostname == "pi-cam-{mac_last_4}".format(**locals())


def _git_hash():
    """Retrieve git hash if it exists
     Args:
        None
     Returns:
        Git hash or error message
    """
    command = "git rev-parse HEAD"

    try:
        command_output = check_output(command, shell=True).decode("utf-8").rstrip()
    except CalledProcessError:
        command_output = '"git rev-parse HEAD" retrieval failed.  No repo?'

    return command_output
