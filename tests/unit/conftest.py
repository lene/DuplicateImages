__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import random
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Generator, List, Tuple

import pillow_heif
import pytest
from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image

WIDTH = 100


def create_image(file: Path, width: int) -> Path:
    height = int(width * 3 / 4)
    color = Color("Black")
    image = Image(width=width, height=height, background=color)
    image.save(filename=file)
    return file


def create_heif_image(file_path: Path, width: int) -> Path:
    height = int(width * 3 / 4)
    heif_file = pillow_heif.from_bytes(
        mode="BGR;16",
        size=(height, width),
        data=bytes([0] * 3 * 2 * width * height)
    )
    with open(file_path, 'wb') as file:
        heif_file.save(fp=file, quality=-1)
    return file_path


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
    copied_file = file.with_suffix(".bak")
    shutil.copyfile(file, copied_file)
    images.append(copied_file)
    return copied_file


def is_pair_found(element1: Path, element2: Path, matches: List[Tuple[Path, Path]]) -> bool:
    return (element1, element2) in matches or (element2, element1) in matches


@pytest.fixture(name="top_directory", scope="session")
def fixture_top_directory() -> Generator[TemporaryDirectory, None, None]:
    top_dir = TemporaryDirectory()
    yield top_dir
    try:
        top_dir.cleanup()
    except FileNotFoundError:
        pass


@pytest.fixture(name="sub_directory", scope="session")
def fixture_sub_directory(top_directory: TemporaryDirectory) -> TemporaryDirectory:
    return TemporaryDirectory(dir=top_directory.name)


@pytest.fixture(scope="session")
def image_files(
        top_directory: TemporaryDirectory, sub_directory: TemporaryDirectory
) -> Generator[List[Path], None, None]:
    images = []
    jpeg_file = create_image(
        Path(NamedTemporaryFile(dir=top_directory.name, prefix="jpeg_", suffix=".jpg").name),
        WIDTH
    )
    images.append(jpeg_file)
    png_file = create_image(
        Path(NamedTemporaryFile(dir=top_directory.name, prefix="png_", suffix=".png").name),
        WIDTH
    )
    images.append(png_file)
    heif_file = create_heif_image(
        Path(NamedTemporaryFile(dir=top_directory.name, prefix="heif_", suffix=".heif").name),
        WIDTH
    )
    images.append(heif_file)
    subdir_file = create_image(
        Path(NamedTemporaryFile(dir=sub_directory.name, prefix="subdir_", suffix=".jpg").name),
        WIDTH
    )
    fill_image_with_random_pixels(subdir_file)
    images.append(subdir_file)
    half_file = create_image(
        Path(
            NamedTemporaryFile(dir=top_directory.name, prefix="test_half_", suffix=".jpg").name
        ),
        WIDTH
    )
    image = Image(filename=half_file)
    image.transform(f'{int(WIDTH / 2)}x{int(WIDTH * 3 / 8)}')
    save(image, half_file)
    images.append(half_file)
    yield images
    for file in images:
        file.unlink(missing_ok=False)
