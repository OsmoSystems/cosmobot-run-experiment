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
AWB_GAINS = (1.307, 1.615)
QUALITY = 100
AWB_MODE = "off"
AWB_QUALITY_CAPTURE_PARAMS = "-q {quality} -awb {awb_mode} -awbg {awb_gains}".format(
    quality=QUALITY,
    awb_mode=AWB_MODE,
    awb_gains=",".join(str(gain) for gain in AWB_GAINS),
)

DEFAULT_EXPOSURE_TIME = 0.8


def capture_with_picamera(
    image_filepath, exposure_time=DEFAULT_EXPOSURE_TIME, warm_up_time=5
):
    resolution = (3280, 2464)
    # framerate is in frames per second
    framerate = int(1 / exposure_time)
    # shutter_speed is in microseconds
    shutter_speed = int(exposure_time * 1000000)
    iso = 100

    camera = picamera.PiCamera()
    # I get out of memory errors when I try to set the resolution
    # camera.resolution = resolution
    camera.start_preview()

    # Camera warm-up time
    print("Sleeping for {}s".format(warm_up_time))
    time.sleep(warm_up_time)

    print("Setting framerate to {}".format(framerate))
    camera.framerate = framerate

    print("Setting shutter_speed to {}".format(shutter_speed))
    camera.shutter_speed = shutter_speed

    print("Setting iso to {}".format(iso))
    camera.iso = 100  # TODO: use variant values

    print("Setting awb params")
    camera.awb_mode = AWB_MODE
    camera.awb_gains = AWB_GAINS

    print("Capturing image using PiCamera")
    camera.capture(image_filepath, bayer=True, quality=QUALITY)
    print("Captured image using PiCamera")

    # Work around https://github.com/waveform80/picamera/issues/528
    # and properly close the camera
    camera.framerate = 1
    camera.close()


def capture_with_raspistill(
    image_filepath,
    exposure_time=DEFAULT_EXPOSURE_TIME,
    warm_up_time=5,
    additional_capture_params="",
):
    """ Capture raw image JPEG+EXIF using command line

    Args:
        image_filepath: filepath where the image will be saved
        exposure_time: number of seconds in the exposure
        warm_up_time: number of seconds to wait for the camera to warm up
        additional_capture_params: Additional parameters to pass to raspistill command

    Returns:
        Resulting command line output of the raspistill command
    """
    exposure_time_microseconds = int(exposure_time * 1e6)
    timeout_milliseconds = int(warm_up_time * 1e3)
    command = (
        'raspistill --raw -o "{image_filepath}"'
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
