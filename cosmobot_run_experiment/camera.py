import pkg_resources
import logging
from subprocess import check_call

# defaults recommended by Pagnutti. These only affect the .jpegs
AWB_QUALITY_CAPTURE_PARAMS = "-q 100 -awb off -awbg 1.307,1.615"


def capture(filename, exposure_time=1.5, timeout_ms=1000, additional_capture_params=""):
    """ Capture raw image JPEG+EXIF using command line

    Args:
        filename: filename to save an image to
        exposure_time: number of seconds in the exposure
        timeout_ms: number of milliseconds to wait for the camera to warm up
        additional_capture_params: Additional parameters to pass to raspistill command

    Returns:
        Resulting command line output of the raspistill command
    """
    exposure_time_microseconds = int(exposure_time * 1000000)
    command = (
        'raspistill --raw -o "{filename}"'
        " {AWB_QUALITY_CAPTURE_PARAMS}"
        " -ss {exposure_time_microseconds}"
        " --timeout {timeout_ms}"
        " {additional_capture_params}"
    ).format(**locals(), **globals())

    logging.info("Capturing image using raspistill: {command}".format(**locals()))
    check_call(command, shell=True)


def simulate_capture_with_copy(filename, timeout_ms=1000, additional_capture_params=""):
    """ Simulate capture by copying image file

    Args:
        filename: filename to copy a test image to
        timeout_ms: ignored, only exists to keep the same signature as `capture()`
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
