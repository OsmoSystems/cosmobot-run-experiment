from mock import sentinel
import pytest

from . import directories as module


@pytest.fixture
def mock_path_exists(mocker):
    return mocker.patch('os.path.exists')


@pytest.fixture
def mock_path_join(mocker):
    return mocker.patch('os.path.join')


@pytest.fixture
def mock_mkdir(mocker):
    return mocker.patch('os.mkdir')


@pytest.fixture
def mock_listdir(mocker):
    return mocker.patch('os.listdir')


class TestCreateOuputDirectory:
    def test_returns_output_directory_path(self, mock_path_exists, mock_path_join, mock_mkdir):
        mock_path_join.return_value = sentinel.expected_output_directory_path

        actual_output_directory_path = module.create_output_directory('/foo/bar', 'baz')

        assert actual_output_directory_path == sentinel.expected_output_directory_path

    def test_creates_output_directory_if_doesnt_exist(self, mock_path_exists, mock_path_join, mock_mkdir):
        mock_path_exists.return_value = False
        mock_path_join.return_value = sentinel.expected_output_directory_path

        module.create_output_directory('/foo/bar', 'baz')

        mock_mkdir.assert_called_with(sentinel.expected_output_directory_path)

    def test_doesnt_create_output_directory_if_exists(self, mock_path_exists, mock_path_join, mock_mkdir):
        mock_path_exists.return_value = True

        module.create_output_directory('/foo/bar', 'baz')

        mock_mkdir.assert_not_called()


def _mock_path_join(path, filename):
    return f'os-path-for-{path}/{filename}'


@pytest.mark.parametrize("name, directory_contents", [
    ('returns filepaths', ['1.jpeg', '2.jpeg']),
    ('sorts filepaths', ['2.jpeg', '1.jpeg']),
    ('filters to extension', ['1.jpeg', '2.jpeg', '1.dng', '2.png']),
])
def test_get_files_with_extension(mock_listdir, mock_path_join, name, directory_contents):
    mock_listdir.return_value = directory_contents
    mock_path_join.side_effect = _mock_path_join

    actual = module.get_files_with_extension('/foo/bar', '.jpeg')
    expected = ['os-path-for-/foo/bar/1.jpeg', 'os-path-for-/foo/bar/2.jpeg']

    assert actual == expected