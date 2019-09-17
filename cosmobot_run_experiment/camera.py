from fractions import Fraction
import logging
import os
import platform
import time
from subprocess import check_call
from typing import Tuple

# Support development without needing pi specific modules installed.
if platform.machine() == "armv7l":
    from picamera import PiCamera  # noqa: E0401  Unable to import
    from cosmobot_run_experiment.set_picamera_gain import set_analog_gain
else:
    logging.warning("Using library stubs for non-raspberry-pi machine")
    from .pi_stubs.picamera import PiCamera


# Default auto-white-balance gains recommended by Pagnutti. These only affect the .jpegs.
# awb_gains are a tuple of values representing the (red, blue) balance of the camera.
PAGNUTTI_AWB_GAINS = (1.307, 1.615)
JPEG_QUALITY = 100

DEFAULT_EXPOSURE_TIME = 0.8
DEFAULT_ISO = 100
DEFAULT_WARM_UP_TIME = 2
DEFAULT_RESOLUTION = (3280, 2464)

# Setting exposure to 0 will use auto-exposure.
# PiCamera hangs for exposures > ~7-8 seconds. See https://github.com/waveform80/picamera/issues/529
VALID_EXPOSURE_RANGE = (0, 6)

# Valid ISOs are hard to pin down. See:
#  - these docs: https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.iso
#  - this github issue: https://github.com/waveform80/picamera/issues/531
# Setting ISO to 0 will use auto-exposure
VALID_ISO_RANGE = (0, 800)


def _wait_for_gains_to_settle(warm_up_time: int):
    """ Sleep for warm_up_time seconds to let the camera 'warm up', i.e. let the analog and digital gains settle
    """
    logging.info("Warming up for {warm_up_time}s".format(**locals()))
    time.sleep(warm_up_time)


class CosmobotPiCamera(PiCamera):
    """ Wraps the existing PiCamera context manager with some protections:
         - an enforced warm up time
         - a capture method that deletes the empty file if an error occurs during capture
         - a bug workaround for closing
    """

    def __enter__(self):
        _wait_for_gains_to_settle(DEFAULT_WARM_UP_TIME)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        # Work around https://github.com/waveform80/picamera/issues/528: set framerate to 1 before closing camera
        logging.debug("Resetting framerate to 1 before close.")
        self.framerate = 1
        super().__exit__(exc_type, exc_value, exc_tb)

    def capture(self, image_filepath, **kwargs):
        """ Cleans up after the parent capture method by deleting empty files

        PiCamera seems to create an empty file first and then fill it. If it is interrupted during the capture
        process we are left with an empty image file that breaks downstream processing code
        """
        try:
            super().capture(image_filepath, **kwargs)
        except KeyboardInterrupt:
            logging.info(
                "KeyboardInterrupt during capture. "
                "Deleting empty file: {image_filepath}".format(**locals())
            )
            os.remove(image_filepath)
            raise


def capture_with_picamera(
    camera: PiCamera,
    image_filepath: str,
    led_on: bool = True,
    exposure_time: float = DEFAULT_EXPOSURE_TIME,
    iso: int = DEFAULT_ISO,
    resolution: Tuple[int] = DEFAULT_RESOLUTION,
    quality: int = JPEG_QUALITY,
    warm_up_time=DEFAULT_WARM_UP_TIME,
):
    """ Capture a PiCamera RAW+JPEG image with specific settings, working around bugs

    In PiCamera's implementation, capture settings have to be set as attributes on the camera instance
    prior to calling the capture() method

    Also, there are some subtleties and bugs that we work around by being careful of the order we set things

    Args:
        camera: a PiCamera instance
        image_filepath: filepath where the image will be saved
        led_on: whether to flash the LED during the exposure. Note: requires pre-configuring firmware using comfigure_picamera_flash.sh
        exposure_time: number of seconds in the exposure
        iso: iso for the exposure
        resolution: resolution for the output jpeg image. Note: increase gpu_mem from 128 to 256 using raspi-config
            to prevent an out of memory error when setting large resolution images, e.g. (3280, 2464)
        quality: the quality of the JPEG encoder as an integer ranging from 1 to 100
    """
    # HACK: co-opt iso for analog_gain setting
    analog_gain = iso
    logging.debug("Setting analog_gain to {analog_gain}".format(**locals()))
    set_analog_gain(camera, analog_gain)

    logging.debug("Setting resolution to {resolution}".format(**locals()))
    camera.resolution = resolution

    flash_mode = "on" if led_on else "off"
    logging.debug("Setting flash_mode to {flash_mode}".format(**locals()))
    camera.flash_mode = flash_mode

    # 1. White balance is controlled by two settings: awb_mode and awb_gains. By setting awb_mode to "off", we can then
    # fix the gains using awb_gains.
    # See https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.awb_mode
    logging.debug(
        "Setting awb_mode to 'off'. "
        "Fixing awb_gains at {PAGNUTTI_AWB_GAINS}".format(**globals())
    )
    camera.awb_mode = "off"
    camera.awb_gains = PAGNUTTI_AWB_GAINS

    # 2. Exposure sensitivity is more complicated. The camera's analog_gain and digital_gains can't be controlled
    # directly, but can be "influenced" by setting ISO and then waiting, giving the gains some time to "settle".
    # Then, we can set exposure_mode to "off" to fix the gains (this must happen *after* setting the ISO)
    # See https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.exposure_mode
    logging.debug("Setting exposure_mode to 'auto' to allow resetting gains")
    camera.exposure_mode = "auto"

    # logging.debug("Setting iso to {iso}".format(**locals()))
    # camera.iso = iso

    # 3. Control the shutter_speed
    # The framerate limits the shutter speed, so it must be set *before* shutter speed
    # https://picamera.readthedocs.io/en/release-1.13/recipes1.html?highlight=framerate#capturing-in-low-light
    framerate = Fraction(1 / exposure_time)  # In frames per second
    logging.debug("Setting framerate to {framerate} fps".format(**locals()))
    camera.framerate = framerate

    shutter_speed = int(exposure_time * 1e6)  # In microseconds
    logging.debug("Setting shutter_speed to {shutter_speed}us".format(**locals()))
    camera.shutter_speed = shutter_speed

    # 4. Give the camera time for the gains to "settle", and then fix them by setting exposure_mode to "off"
    _wait_for_gains_to_settle(warm_up_time)

    logging.debug("Setting exposure_mode to 'off'")
    camera.exposure_mode = "off"

    logging.info("Capturing PiCamera image to {image_filepath}".format(**locals()))
    camera.capture(image_filepath, bayer=True, quality=quality)
    logging.debug("Captured PiCamera image")


def capture_with_raspistill(
    image_filepath,
    exposure_time=DEFAULT_EXPOSURE_TIME,
    iso=DEFAULT_ISO,
    quality=JPEG_QUALITY,
    warm_up_time=DEFAULT_WARM_UP_TIME,
    additional_capture_params="",
):
    """ Capture raw image JPEG+EXIF using command line

    Args:
        image_filepath: filepath where the image will be saved
        exposure_time: number of seconds in the exposure
        quality: the quality of the JPEG encoder as an integer ranging from 1 to 100
        warm_up_time: number of seconds to wait for the camera to warm up
        additional_capture_params: Additional parameters to pass to raspistill command

    Returns:
        Resulting command line output of the raspistill command
    """
    exposure_time_microseconds = int(exposure_time * 1e6)
    timeout_milliseconds = int(warm_up_time * 1e3)
    awb_gains_str = ",".join(map(str, PAGNUTTI_AWB_GAINS))

    command = (
        'raspistill --raw -o "{image_filepath}"'
        ' -q {quality} -awb "off" -awbg {awb_gains_str}'
        " -ss {exposure_time_microseconds}"
        " -ISO {iso}"
        " --timeout {timeout_milliseconds}"
        " {additional_capture_params}"
    ).format(**locals(), **globals())

    logging.info("Capturing image using raspistill: {command}".format(**locals()))
    check_call(command, shell=True)
