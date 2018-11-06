import os


def get_base_output_path():
    return os.path.expanduser('~/camera-sensor-output/')


def iso_datetime_for_filename(datetime):
    ''' Returns datetime as a ISO-ish format string that can be used in filenames (which can't inclue ":")
        datetime(2018, 1, 1, 12, 1, 1) --> '2018-01-01--12-01-01'
    '''
    return datetime.strftime('%Y-%m-%d--%H-%M-%S')
