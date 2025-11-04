# pylint: disable=missing-docstring
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import random
import shutil
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory, mkdtemp
from typing import Generator, List, Tuple
from unittest.mock import Mock

from pillow_heif import from_bytes, HeifFile
import pytest
from imagehash import ImageHash
from numpy import array
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image

IMAGE_WIDTH = 40
MOCK_IMAGE_HASH_VALUE = ImageHash(array([[True, True], [True, True]]))  # just some random value
mock_algorithm = Mock(return_value=MOCK_IMAGE_HASH_VALUE)


def create_image(file: Path, width: int) -> Path:
    if file.suffix == '.heif':
        return create_heif_image(file, width)
    height = int(width * 3 / 4)
    color = Color('Black')
    image = Image(width=width, height=height, background=color)
    image.save(filename=file)
    return file


def create_heif_image(file_path: Path, width: int) -> Path:
    with open(file_path, 'wb') as file:
        _generate_heif_bytes(width).save(fp=file, quality=-1)
    return file_path


def _generate_heif_bytes(width: int) -> HeifFile:
    height = width * 3 // 4
    return from_bytes(
        mode='BGR;16',
        size=(height, width),
        data=bytes([0] * 3 * 2 * width * height)
    )


def create_corrupt_heif_image(file: Path, width: int) -> Path:
    """
    Creates a corrupt HEIF file that can be opened but fails during decoding.

    This creates a more subtle corruption - the file structure is intact enough
    for PIL to identify it as HEIF, but the image data is corrupted so decoding fails.
    """
    # create a valid HEIF file in memory buffer
    buffer = BytesIO()
    _generate_heif_bytes(width).save(fp=buffer, quality=-1)
    data = bytearray(buffer.getvalue())

    # Corrupt the image data section with a much more subtle corruption
    # We corrupt just a few bytes deep in the file to trigger decoder errors
    # while keeping the file structure intact
    corruption_start = len(data) * 3 // 4  # Start corruption in last quarter
    corruption_end = corruption_start + 8  # Corrupt only 8 bytes
    if corruption_end < len(data):
        # Use pattern corruption instead of all 0xFF to avoid making it unidentifiable
        for i in range(corruption_start, corruption_end):
            data[i] = (data[i] + 128) % 256  # Flip the high bit

    # Write corrupted data to file
    with open(file, 'wb') as file:
        file.write(data)

    return file


def fill_image_with_random_pixels(file: Path, seed: int = 0) -> None:
    random.seed(seed)
    image = Image(filename=file)
    with Drawing() as draw:
        for x in range(0, image.size[0]):
            for y in range(0, image.size[1]):
                color = Color(f'rgb({random_short()},{random_short()},{random_short()}')
                draw.fill_color = color
                draw.point(x, y)
            draw(image)
    image.save(filename=file)


def named_file(name: str, images: List[Path]) -> Path:
    return next(filter(lambda f: name + '_' in f.name, images))


def random_short() -> int:
    return random.randrange(65535)  # noqa: S311


def save(image: Image, path: Path) -> None:
    """
    Save image without letting the wand module create a backup file (which would
    confuse tearDownClass()
    """
    with path.open('wb') as file:
        image.save(file=file)


def delete_image_file(file: Path, images: List[Path]) -> None:
    file.unlink()
    images.remove(file)


def copy_image_file(file: Path, images: List[Path]) -> Path:
    copied_file = file.with_suffix('.bak')
    shutil.copyfile(file, copied_file)
    images.append(copied_file)
    return copied_file


def is_pair_found(element1: Path, element2: Path, matches: List[Tuple[Path, Path]]) -> bool:
    return (element1, element2) in matches or (element2, element1) in matches


@pytest.fixture(name='top_directory', scope='session')
def fixture_top_directory() -> Generator[TemporaryDirectory, None, None]:
    top_dir = TemporaryDirectory()
    yield top_dir
    try:
        top_dir.cleanup()
    except FileNotFoundError:
        pass


@pytest.fixture(name='sub_directory', scope='session')
def fixture_sub_directory(top_directory: TemporaryDirectory) -> TemporaryDirectory:
    return TemporaryDirectory(dir=top_directory.name)


def create_jpg_and_png(top_directory: TemporaryDirectory) -> List[Path]:
    images = []
    jpeg_file = create_image(
        Path(NamedTemporaryFile(dir=top_directory.name, prefix='jpeg_', suffix='.jpg').name),
        IMAGE_WIDTH
    )
    images.append(jpeg_file)
    png_file = create_image(
        Path(NamedTemporaryFile(dir=top_directory.name, prefix='png_', suffix='.png').name),
        IMAGE_WIDTH
    )
    images.append(png_file)
    return images


def create_half_jpg(top_directory: TemporaryDirectory) -> Path:
    half_file = create_image(
        Path(
            NamedTemporaryFile(dir=top_directory.name, prefix='test_half_', suffix='.jpg').name
        ),
        IMAGE_WIDTH
    )
    image = Image(filename=half_file)
    image.transform(f'{int(IMAGE_WIDTH / 2)}x{int(IMAGE_WIDTH * 3 / 8)}')
    save(image, half_file)
    return half_file


@pytest.fixture(scope='session')
def image_files(
        top_directory: TemporaryDirectory, sub_directory: TemporaryDirectory
) -> Generator[List[Path], None, None]:
    images = create_jpg_and_png(top_directory)
    heif_file = create_heif_image(
        Path(NamedTemporaryFile(dir=top_directory.name, prefix='heif_', suffix='.heif').name),
        IMAGE_WIDTH
    )
    images.append(heif_file)
    subdir_file = create_image(
        Path(NamedTemporaryFile(dir=sub_directory.name, prefix='subdir_', suffix='.jpg').name),
        IMAGE_WIDTH
    )
    fill_image_with_random_pixels(subdir_file)
    images.append(subdir_file)
    half_file = create_half_jpg(top_directory)
    images.append(half_file)
    yield images
    for file in images:
        file.unlink(missing_ok=False)


@pytest.fixture
def reset_call_count():
    mock_algorithm.call_count = 0


@pytest.fixture
def hash_store_path(file_type: str) -> Path:
    top_directory = Path(mkdtemp())
    return Path(NamedTemporaryFile(dir=top_directory, suffix=f'.{file_type}').name)
