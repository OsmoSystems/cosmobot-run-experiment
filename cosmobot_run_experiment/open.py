from picamraw import PiRawBayer, PiCameraVersion

RAW_BIT_DEPTH = 2**10


def as_rgb(raw_image_path):
    ''' Extracts the raw bayer data from a JPEG+RAW file and converts it to an
        `RGB Image` (see definition in README).

        NOTE: Duplicated from process_experiment

    Args:
        raw_image_path: The full path to the JPEG+RAW file

    Returns:
        An `RGB Image`
    '''
    raw_bayer = PiRawBayer(
        filepath=raw_image_path,
        camera_version=PiCameraVersion.V2,
        sensor_mode=0
    )

    # Divide by the bit-depth of the raw data to normalize into the (0,1) range
    rgb_image = raw_bayer.to_rgb() / RAW_BIT_DEPTH

    return rgb_image
