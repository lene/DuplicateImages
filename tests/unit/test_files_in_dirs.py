__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator
from unittest.mock import patch

import pytest

from duplicate_images.duplicate import files_in_dirs, is_image_file
from .conftest import create_image

NUM_NUMBERED_FILES = 3
TEST_IMAGE_WIDTH = 40


@pytest.fixture(name='temp_dir', scope='session')
def top_folder() -> Generator[Path, None, None]:
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(name='filled_folder', scope='session')
def filled_temp_dir(temp_dir: Path) -> Generator[Path, None, None]:
    for i in range(NUM_NUMBERED_FILES):
        (temp_dir / str(i)).mkdir()
        (temp_dir / str(i) / f'{i}.txt').open('w').close()
    yield temp_dir


def test_files_in_dirs_finds_created_empty_files(filled_folder: Path) -> None:
    found = files_in_dirs([filled_folder])
    assert NUM_NUMBERED_FILES == len(found)
    assert sorted(found) == sorted(filled_folder.glob('?/?.txt'))


def test_files_in_dirs_ignores_empty_files_if_looking_for_images(filled_folder: Path) -> None:
    found = files_in_dirs([filled_folder], is_image_file)
    assert not found


def test_files_in_dirs_ignores_subdir_matching_number_regex(filled_folder: Path) -> None:
    found = files_in_dirs([filled_folder], exclude_regexes=[r'/\d$'])
    assert not found


def test_files_in_dirs_ignores_subdir_matching_explicit_name(filled_folder: Path) -> None:
    assert NUM_NUMBERED_FILES >= 1
    found = files_in_dirs([filled_folder], exclude_regexes=['/1$'])
    assert NUM_NUMBERED_FILES - 1 == len(found)


def test_files_in_dirs_ignores_subdirs_matching_multiple_names(filled_folder: Path) -> None:
    assert NUM_NUMBERED_FILES >= 2
    found = files_in_dirs([filled_folder], exclude_regexes=['/1$', '/2$'])
    assert NUM_NUMBERED_FILES - 2 == len(found)


def test_files_in_dirs_ignores_patterns_in_file_names(filled_folder: Path) -> None:
    assert NUM_NUMBERED_FILES >= 1
    found = files_in_dirs([filled_folder], exclude_regexes=['/1.txt$'])
    assert NUM_NUMBERED_FILES == len(found)


def test_files_in_dirs_with_arbitrary_condition(filled_folder: Path) -> None:
    assert NUM_NUMBERED_FILES >= 2
    found = files_in_dirs([filled_folder], is_file=lambda f: '2.txt' == f.name)
    assert 1 == len(found)
    assert '2.txt' == found[0].name


def test_is_image_file_empty_file(filled_folder: Path) -> None:
    assert not is_image_file(filled_folder / '1' / '1.txt')


@pytest.mark.parametrize('extension', ['jpg', 'png', 'heif'])
def test_is_image_file_image_file(temp_dir: Path, extension: str) -> None:
    create_image(temp_dir / f'1.{extension}', TEST_IMAGE_WIDTH)
    assert is_image_file(temp_dir / f'1.{extension}')


@pytest.mark.parametrize('extension', ['jpg', 'png', 'heif'])
def test_is_image_file_with_os_failure(temp_dir: Path, extension: str) -> None:
    create_image(temp_dir / f'1.{extension}', TEST_IMAGE_WIDTH)
    with patch('builtins.open', side_effect=OSError()):
        assert not is_image_file(temp_dir / f'1.{extension}')
