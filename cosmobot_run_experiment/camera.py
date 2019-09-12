from fractions import Fraction
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
DEFAULT_WARM_UP_TIME = 5

MICROSECONDS_PER_SECOND = 1000000


class PiCameraWithSafeClose(picamera.PiCamera):
    def __exit__(self):
        print("resetting framerate before close...")
        self.framerate = 1
        print("new framerate: ", self.framerate)
        self.close()


def capture_with_picamera(
    image_filepath,
    exposure_time=DEFAULT_EXPOSURE_TIME,
    warm_up_time=DEFAULT_WARM_UP_TIME,
):
    with PiCameraWithSafeClose() as camera:
        # Had to update gpu_mem (from 128 to 256) using raspi-config to prevent an out of memory error.
        # TODO: update provisioing script with this: sudo raspi-config nonint do_memory_split 256
        resolution = (3280, 2464)
        shutter_speed = int(exposure_time * MICROSECONDS_PER_SECOND)  # In microseconds
        framerate = Fraction(
            MICROSECONDS_PER_SECOND, shutter_speed
        )  # In frames per second
        iso = 100

        # TODO: initialize camera and perform warmup only once
        camera.resolution = resolution
        camera.start_preview()

        logging.debug("Warming up for {warm_up_time}s".format(**locals()))
        time.sleep(warm_up_time)

        # The framerate limits the shutter speed, so it must be set *before* shutter speed
        # https://picamera.readthedocs.io/en/release-1.13/recipes1.html?highlight=framerate#capturing-in-low-light
        logging.debug("Setting framerate to {framerate} fps".format(**locals()))
        camera.framerate = framerate

        # TODO: protect against shutter speeds >8s (bug causes it to hang)
        # https://github.com/waveform80/picamera/issues/529
        logging.debug("Setting shutter_speed to {shutter_speed}us".format(**locals()))
        camera.shutter_speed = shutter_speed

        logging.debug("Setting iso to {iso}".format(**locals()))
        camera.iso = 100  # TODO: use variant values

        logging.debug(
            "Setting awb to {AWB_MODE} {AWB_GAINS}".format(**locals(), **globals())
        )
        camera.awb_mode = AWB_MODE
        camera.awb_gains = AWB_GAINS

        logging.info("Capturing image using PiCamera")
        camera.capture(image_filepath, bayer=True, quality=QUALITY)
        logging.debug("Captured image using PiCamera")

        # # Work around https://github.com/waveform80/picamera/issues/528: set framerate back to 1 before closing camera
        # camera.framerate = 1
        #
        # # TODO: ensure camera gets closed even if another error occurs
        # camera.close()


def capture_with_raspistill(
    image_filepath,
    exposure_time=DEFAULT_EXPOSURE_TIME,
    warm_up_time=DEFAULT_WARM_UP_TIME,
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
