import pkg_resources
from subprocess import check_call

AWB_QUALITY_CAPTURE_PARAMS = '-q 100 -awb off -awbg 1.307,1.615'  # defaults recommended by Pagnutti


def capture(filename, additional_capture_params=''):
    ''' Capture raw image JPEG+EXIF using command line

    Args:
        filename: filename to save an image to
        additional_capture_params: Additional parameters to pass to raspistill command

    Returns:
        Resulting command line output of the raspistill command
    '''
    command = f'raspistill --raw -o "{filename}" {additional_capture_params} {AWB_QUALITY_CAPTURE_PARAMS}'
    print(f'Capturing image using raspistill: {command}')
    check_call(command, shell=True)


def simulate_capture_with_copy(filename, **kwargs):
    ''' Simulate capture by copying image file

    Args:
        filename: filename to copy a test image to

    Returns:
        Resulting command line output of the copy command
    '''
    test_image_path = pkg_resources.resource_filename(__name__, 'v2_image_for_development.jpeg')
    command = f'cp "{test_image_path}" "{filename}"'
    print(f'Simulate capture: {command}')
    check_call(command, shell=True)
