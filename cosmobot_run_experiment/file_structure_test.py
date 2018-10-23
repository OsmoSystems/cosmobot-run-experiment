from datetime import datetime

from . import file_structure as module


class TestIsoDatetimeForFilename:
    def test_returns_iso_ish_string(self):
        actual = module.iso_datetime_for_filename(datetime(2018, 1, 2, 13, 14, 15))
        expected = '2018-01-02--13-14-15'

        assert actual == expected
