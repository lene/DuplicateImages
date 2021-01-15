import unittest
import tempfile
import random
import shutil
from pathlib import Path
from typing import List, Tuple

from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image

from duplicate_images import duplicate


def create_image(file: Path, width: int) -> Path:
    height = int(width * 3 / 4)
    color = Color("Black")
    image = Image(width=width, height=height, background=color)
    image.save(filename=file)
    return file


def random_short() -> int:
    return random.randrange(65535)  # noqa: S311


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


def save(image: Image, path: Path) -> None:
    """
    Save imqge without letting the wand module create a backup file (which would
    confuse tearDownClass()
    """
    with path.open('wb') as file:
        image.save(file=file)


class SetupImages(unittest.TestCase):

    width = 100
    ASPECT_FUZZINESS = 0.05
    RMS_ERROR = 0.05
    OPTIONS = {'aspect_fuzziness': ASPECT_FUZZINESS, 'rms_error': RMS_ERROR}

    top_directory = Path()
    sub_directory = Path()
    image_files: List[Path] = []
    jpeg_file = Path()
    png_file = Path()
    half_file = Path()
    noisy_file = Path()
    subdir_file = Path()

    to_create = {'jpeg', 'png', 'subdir', 'half'}
    tolerate_deleted_files = False

    @classmethod
    def setUpClass(cls) -> None:
        """create a number of temporary image files"""
        cls.top_directory = Path(tempfile.mkdtemp())
        cls.image_files = []
        if 'jpeg' in cls.to_create:
            cls.jpeg_file = create_image(
                Path(tempfile.mkstemp(dir=cls.top_directory, prefix="jpeg_", suffix=".jpg")[1]),
                cls.width
            )
            cls.image_files.append(cls.jpeg_file)
        if 'png' in cls.to_create:
            cls.png_file = create_image(
                Path(tempfile.mkstemp(dir=cls.top_directory, prefix="png_", suffix=".png")[1]),
                cls.width
            )
            cls.image_files.append(cls.png_file)
        if 'subdir' in cls.to_create:
            cls.sub_directory = Path(tempfile.mkdtemp(dir=cls.top_directory))
            cls.subdir_file = create_image(
                Path(tempfile.mkstemp(dir=cls.sub_directory, prefix="subdir_", suffix=".jpg")[1]),
                cls.width
            )
            fill_image_with_random_pixels(cls.subdir_file)
            cls.image_files.append(cls.subdir_file)
        if 'half' in cls.to_create:
            cls.half_file = create_image(
                Path(
                    tempfile.mkstemp(dir=cls.top_directory, prefix="test_half_", suffix=".jpg")[1]
                ),
                cls.width
            )
            image = Image(filename=cls.half_file)
            image.transform('{}x{}'.format(int(cls.width / 2), int(cls.width * 3 / 8)))
            save(image, cls.half_file)
            cls.image_files.append(cls.half_file)

    @classmethod
    def tearDownClass(cls) -> None:
        """"remove all the files created by setUp"""
        for file in cls.image_files:
            file.unlink(missing_ok=cls.tolerate_deleted_files)
        if 'subdir' in cls.to_create:
            cls.sub_directory.rmdir()
        cls.top_directory.rmdir()

    def get_image_files(self) -> List[Path]:
        return sorted(duplicate.files_in_dirs([self.top_directory]))

    def copy_image_file(self, file: Path) -> Path:
        copied_file = file.with_suffix(".bak")
        shutil.copyfile(file, copied_file)
        self.image_files.append(copied_file)
        return copied_file

    def delete_image_file(self, file: Path) -> None:
        file.unlink()
        self.image_files.remove(file)

    @staticmethod
    def is_pair_found(element1: Path, element2: Path, matches: List[Tuple[Path, Path]]) -> bool:
        return (element1, element2) in matches or (element2, element1) in matches
