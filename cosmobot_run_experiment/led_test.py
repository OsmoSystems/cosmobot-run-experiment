import pytest
from . import led as module


class TestLed:
    @pytest.mark.parametrize("name, args_in", [
        ('1', ['--color','red'])
    ])
    def test_set_led(self, name, args_in):
        module.set_led(args_in)
        assert True
