import logging
import pkg_resources
import platform
import time
from subprocess import check_call

# Support development without needing pi specific modules installed.
if platform.machine() == "armv7l":
    import picamera  # noqa: E0401  Unable to import
else:
    logging.warning("Using library stubs for non-raspberry-pi machine")
    # TODO: stub for local development

# defaults recommended by Pagnutti. These only affect the .jpegs
AWB_QUALITY_CAPTURE_PARAMS = "-q 100 -awb off -awbg 1.307,1.615"

DEFAULT_EXPOSURE_TIME = 0.8


def capture_with_picamera(
    image_filepath, exposure_time=DEFAULT_EXPOSURE_TIME, warm_up_time=5
):
    # TODO: constant for resolution
    resolution = (3280, 2464)
    framerate = 1 / exposure_time
    shutter_speed = int(exposure_time * 1000000)
    iso = 100

    camera = picamera.PiCamera(resolution=resolution)
    logging.debug("Preparing to capture {}".format(image_filepath))

    # Important to set framerate before shutter_speed, since framerate limits shutter speed
    # https://picamera.readthedocs.io/en/release-1.13/recipes1.html#capturing-in-low-light
    logging.debug("Setting framerate to {}".format(framerate))
    camera.framerate = framerate

    logging.debug("Starting preview")
    camera.start_preview()
    # Camera warm-up time # TODO: do this just once
    logging.debug("Letting it warm up for {}s".format(warm_up_time))
    time.sleep(warm_up_time)

    logging.debug("Setting shutter_speed to {}".format(shutter_speed))
    camera.shutter_speed = shutter_speed

    logging.debug("Setting iso to {}".format(iso))
    camera.iso = 100  # TODO: use variant values

    logging.debug("Setting awb params")
    camera.awb_mode = "off"
    camera.awb_gains = [1.307, 1.615]

    logging.info("Capturing image using PiCamera")
    camera.capture(image_filepath, bayer=True, quality=100)
    logging.debug("Captured image using PiCamera")

    # TODO: probably make this a context manager
    # Work around https://github.com/waveform80/picamera/issues/528
    # and properly close the camera
    camera.framerate = 1
    camera.close()


def capture(
    filename,
    exposure_time=DEFAULT_EXPOSURE_TIME,
    warm_up_time=5,
    additional_capture_params="",
):
    """ Capture raw image JPEG+EXIF using command line

    Args:
        filename: filename to save an image to
        exposure_time: number of seconds in the exposure
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
