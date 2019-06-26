import pkg_resources
import logging
from subprocess import check_call

AWB_QUALITY_CAPTURE_PARAMS = (
    "-q 100 -awb off -awbg 1.307,1.615"
)  # defaults recommended by Pagnutti


def capture(filename, additional_capture_params=""):
    """ Capture raw image JPEG+EXIF using command line

    Args:
        filename: filename to save an image to
        additional_capture_params: Additional parameters to pass to raspistill command

    Returns:
        Resulting command line output of the raspistill command
    """
    command = 'raspistill --raw -o "{filename}" {AWB_QUALITY_CAPTURE_PARAMS} {additional_capture_params}'.format(
        **locals(), **globals()
    )
    logging.info("Capturing image using raspistill: {command}".format(**locals()))
    check_call(command, shell=True)


def simulate_capture_with_copy(filename, additional_capture_params=""):
    """ Simulate capture by copying image file

    Args:
        filename: filename to copy a test image to
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
