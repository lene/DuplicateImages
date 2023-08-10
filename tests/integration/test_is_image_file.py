from pathlib import Path
from typing import List

import pytest

from duplicate_images.duplicate import is_image_file


def base_dir() -> Path:
    return Path(__file__).resolve().parent / 'data' / 'is_image_file'


def image_files() -> List[Path]:
    return list((base_dir() / 'is_image').glob('test.*'))


def not_image_files() -> List[Path]:
    return list((base_dir() / 'is_not_image').glob('test.*'))


@pytest.mark.parametrize('image_file', image_files())
def test_image_files_are_recognized(image_file: Path) -> None:
    assert is_image_file(image_file)


@pytest.mark.parametrize('not_image_file', not_image_files())
def test_non_image_files_are_recognized(not_image_file: Path) -> None:
    assert not is_image_file(not_image_file)
