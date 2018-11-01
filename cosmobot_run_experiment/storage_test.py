import pytest
from . import storage as module


@pytest.fixture
def mock_get_free_disk_space(mocker):
    get_free_disk_space = mocker.patch.object(module, '_get_free_disk_space_bytes')
    return get_free_disk_space


class TestHowManyImagesWithFreeSpace:
    @pytest.mark.parametrize("test_name,free_space,expected", [
        ('no space!', 0, 0),
        ('one image', module.IMAGE_SIZE_IN_BYTES, 1),
        ('one image - should round down', module.IMAGE_SIZE_IN_BYTES * 1.7, 1),
        ('two images', module.IMAGE_SIZE_IN_BYTES * 2, 2),
    ])
    def test_basic_cases(self, mock_get_free_disk_space, test_name, free_space, expected):
        mock_get_free_disk_space.return_value = free_space

        assert module.how_many_images_with_free_space() == expected

    def test_lots_of_space(self, mock_get_free_disk_space):
        mock_get_free_disk_space.return_value = 1e12
        a_thousand = 1e3
        assert module.how_many_images_with_free_space() > a_thousand


class TestFreeSpaceForOneImage:
    @pytest.mark.parametrize("test_name,free_space,expected", [
        ('no space!', 0, False),
        ('not quite enough space', module.IMAGE_SIZE_IN_BYTES - 1, False),
        ('exactly enough space', module.IMAGE_SIZE_IN_BYTES, True),
        ('some extra space', module.IMAGE_SIZE_IN_BYTES + 2, True),
    ])
    def test_basic_cases(self, mock_get_free_disk_space, test_name, free_space, expected):
        mock_get_free_disk_space.return_value = free_space

        assert module.free_space_for_one_image() == expected
