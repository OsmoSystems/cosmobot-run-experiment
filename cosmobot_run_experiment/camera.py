from fractions import Fraction
import logging
import os
import platform
import time
from subprocess import check_call
from typing import Tuple

import numpy as np

# Support development without needing pi specific modules installed.
if platform.machine() == "armv7l":
    from picamera import PiCamera, mmal, exc  # noqa: E0401  Unable to import
    from picamera.mmalobj import to_rational
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
# Since we've had to work around multiple issues, our workaround only applies between ISO 54 and 500
VALID_ISO_RANGE = (54, 500)


def _wait_for_warm_up(warm_up_time: int):
    """ Sleep for warm_up_time seconds to let the camera 'warm up', i.e. let the analog and digital gains settle
    """
    logging.info(f"Warming up for {warm_up_time}s")
    time.sleep(warm_up_time)


def _get_analog_gain_from_iso(iso):
    """
    This function maps from an ISO to a desired actual analog_gain, working around the fact that
    PiCamera doesn't seem to properly fix the analog_gain for a given ISO.
    The mapping used here is a linear function that appears to fit the data between ISO=54 and ISO=500.
    The function is defined by the two endpoints:
        ISO     analog_gain     comment
        54      1               PiCamera docs suggest this should be ISO 60, but experimentally we found 54
        579.678 2731/256        Experimentally determined - the analog gain maxes out here
        800     14.72           From PiCamera docs. The line through this fits our experimental data up to ISO 500

    See detailed analysis here: https://github.com/waveform80/picamera/issues/531
    """
    reference_isos = [54, 579.678]
    reference_analog_gains = [1, 2731 / 256]

    return np.interp(iso, reference_isos, reference_analog_gains)


class CosmobotPiCamera(PiCamera):
    """ Wraps the existing PiCamera context manager with some protections:
         - an enforced warm up time
         - a capture method that uses a temporary file to protect against errors during capture
         - analog_gain and digital_gain properties that allow directly setting the gains
         - a bug workaround for closing
    """

    def __enter__(self):
        _wait_for_warm_up(DEFAULT_WARM_UP_TIME)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        # Work around https://github.com/waveform80/picamera/issues/528: set framerate to 1 before closing camera
        logging.debug("Resetting framerate to 1 before close.")
        self.framerate = 1
        super().__exit__(exc_type, exc_value, exc_tb)

    # Inspired by this gist: https://gist.github.com/rwb27/a23808e9f4008b48de95692a38ddaa08/
    # with small modifications
    def _set_gain(self, gain_type, gain):
        """Set the analog or digital gain of a PiCamera.

        gain_type: either MMAL_PARAMETER_ANALOG_GAIN or MMAL_PARAMETER_DIGITAL_GAIN
        gain: a numeric value that can be converted to a rational number.
        """
        return_code = mmal.mmal_port_parameter_set_rational(
            self._camera.control._port, gain_type, to_rational(gain)
        )
        if return_code == 4:
            raise exc.PiCameraMMALError(
                return_code,
                "Are you running the latest version of the userland libraries? "
                "Gain setting was introduced in late 2017.",
            )
        elif return_code != 0:
            raise exc.PiCameraMMALError(return_code)

    def _set_analog_gain(self, analog_gain):
        MMAL_PARAMETER_ANALOG_GAIN = mmal.MMAL_PARAMETER_GROUP_CAMERA + 0x59
        self._set_gain(MMAL_PARAMETER_ANALOG_GAIN, analog_gain)

    analog_gain = property(PiCamera._get_analog_gain, _set_analog_gain)

    def _set_digital_gain(self, analog_gain):
        MMAL_PARAMETER_DIGITAL_GAIN = mmal.MMAL_PARAMETER_GROUP_CAMERA + 0x5A
        self._set_gain(MMAL_PARAMETER_DIGITAL_GAIN, analog_gain)

    digital_gain = property(PiCamera._get_digital_gain, _set_digital_gain)

    def capture(self, image_filepath, **kwargs):
        """ Cleans up after the parent capture method by saving to a temporary file first, and only renaming if capture
        succeeds

        PiCamera seems to create an empty file first and then fill it. If it is interrupted during the capture
        process we are left with an empty image file that breaks downstream processing code.
        """

        # Note: this means output format must be specified explicitly, as the "~" confuses the mimetype guesser
        tmp_image_filepath = f"{image_filepath}~"
        super().capture(tmp_image_filepath, **kwargs)
        os.rename(tmp_image_filepath, image_filepath)


def capture_with_picamera(
    camera: CosmobotPiCamera,
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
        led_on: whether to flash the LED during the exposure. Note: requires pre-configuring firmware
        exposure_time: number of seconds in the exposure
        iso: iso for the exposure
        resolution: resolution for the output jpeg image. Note: increase gpu_mem from 128 to 256 using raspi-config
            to prevent an out of memory error when setting large resolution images, e.g. (3280, 2464)
        quality: the quality of the JPEG encoder as an integer ranging from 1 to 100
    """
    logging.debug(f"Setting resolution to {resolution}")
    camera.resolution = resolution

    flash_mode = "on" if led_on else "off"
    logging.debug(f"Setting flash_mode to {flash_mode}")
    camera.flash_mode = flash_mode

    # 1. White balance is controlled by two settings: awb_mode and awb_gains. By setting awb_mode to "off", we can then
    # fix the gains using awb_gains.
    # See https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.awb_mode
    logging.debug(
        f"Setting awb_mode to 'off'. Fixing awb_gains at {PAGNUTTI_AWB_GAINS}"
    )
    camera.awb_mode = "off"
    camera.awb_gains = PAGNUTTI_AWB_GAINS

    # 2. Exposure sensitivity is more complicated. PiCamera's analog_gain and digital_gains can't be controlled
    # directly, but can be "influenced" by setting ISO and then waiting, giving the gains some time to "settle".
    # Then, theoretically we can set exposure_mode to "off" to fix the gains (this must happen *after* setting the ISO)
    # See https://picamera.readthedocs.io/en/release-1.13/api_camera.html#picamera.PiCamera.exposure_mode

    # However, in practice this never worked. Instead we updated our CosmobotPiCamera wrapper with the ability to set
    # the analog_gain directly, and calculate the appropriate analog_gain given the desired iso (to match the docs and
    # what we get through raspistill)

    analog_gain = _get_analog_gain_from_iso(iso)
    logging.debug(f"Desired ISO: {iso}")
    logging.debug(f"Setting analog_gain to {analog_gain}")
    camera.analog_gain = analog_gain

    # 3. Control the shutter_speed
    # The framerate limits the shutter speed, so it must be set *before* shutter speed
    # https://picamera.readthedocs.io/en/release-1.13/recipes1.html?highlight=framerate#capturing-in-low-light
    framerate = Fraction(1 / exposure_time)  # In frames per second
    logging.debug(f"Setting framerate to {framerate} fps")
    camera.framerate = framerate

    shutter_speed = int(exposure_time * 1e6)  # In microseconds
    logging.debug(f"Setting shutter_speed to {shutter_speed}us")
    camera.shutter_speed = shutter_speed

    # 4. Give the camera time for the gains to "settle", and then fix them by setting exposure_mode to "off"
    _wait_for_warm_up(warm_up_time)

    logging.debug("Setting exposure_mode to 'off'")
    camera.exposure_mode = "off"

    logging.info(f"Capturing PiCamera image to {image_filepath}")
    camera.capture(image_filepath, format="jpeg", bayer=True, quality=quality)
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
        " -q {quality} -awb off -awbg {awb_gains_str}"
        " -ss {exposure_time_microseconds}"
        " -ISO {iso}"
        " --timeout {timeout_milliseconds}"
        " {additional_capture_params}"
    ).format(**locals(), **globals())

    logging.info("Capturing image using raspistill: {command}".format(**locals()))
    check_call(command, shell=True)
