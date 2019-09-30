import pkg_resources
import logging
from subprocess import check_call

# defaults recommended by Pagnutti. These only affect the .jpegs
AWB_QUALITY_CAPTURE_PARAMS = "-q 100 -awb off -awbg 1.307,1.615"

DEFAULT_EXPOSURE_TIME = 0.8
DEFAULT_ISO = 100
DEFAULT_WARM_UP_TIME = 5


def capture(
    filename,
    exposure_time=DEFAULT_EXPOSURE_TIME,
    iso=DEFAULT_ISO,
    warm_up_time=DEFAULT_WARM_UP_TIME,
    additional_capture_params="",
):
    """ Capture raw image JPEG+EXIF using command line

    Args:
        filename: filename to save an image to
        exposure_time: number of seconds in the exposure
        iso: the ISO setting
        warm_up_time: number of seconds to wait for the camera to warm up
        additional_capture_params: Additional parameters to pass to raspistill command

    Returns:
        Resulting command line output of the raspistill command
    """
    exposure_time_microseconds = int(exposure_time * 1e6)
    timeout_milliseconds = int(warm_up_time * 1e3)
    command = (
        'raspistill --raw -o "{filename}"'
        " {AWB_QUALITY_CAPTURE_PARAMS}"
        " -ss {exposure_time_microseconds}"
        " -ISO {iso}"
        " --timeout {timeout_milliseconds}"
        " {additional_capture_params}"
    ).format(**locals(), **globals())

    logging.info("Capturing image using raspistill: {command}".format(**locals()))
    check_call(command, shell=True)


def simulate_capture_with_copy(
    filename, exposure_time=None, warm_up_time=None, additional_capture_params=""
):
    """ Simulate capture by copying image file

    Args:
        filename: filename to copy a test image to
        exposure_time: ignored, only exists to keep the same signature as `capture()`
        warm_up_time: ignored, only exists to keep the same signature as `capture()`
        additional_capture_params: ignored, only exists to keep the same signature as `capture()`

    Returns:
        Resulting command line output of the copy command
    """
    test_image_path = pkg_resources.resource_filename(
        __name__, "v2_image_for_development.jpeg"
    )
    command = 'cp "{test_image_path}" "{filename}"'.format(**locals())
    logging.info("Simulate capture: {command}".format(**locals()))
    check_call(command, shell=True)
