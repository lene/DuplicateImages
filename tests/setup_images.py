import unittest
import tempfile
import random
import os
from typing import List

from wand.color import Color
from wand.drawing import Drawing
from wand.image import Image

from duplicate_images import duplicate


def create_image(filename: str, width: int) -> str:
    height = int(width * 3 / 4)
    color = Color("Black")
    image = Image(width=width, height=height, background=color)
    image.save(filename=filename)
    return filename


def random_short() -> int:
    return random.randrange(65535)


def fill_image_with_random_pixels(filename: str) -> None:
    random.seed(0)
    image = Image(filename=filename)
    with Drawing() as draw:
        for x in range(0, image.size[0]):
            for y in range(0, image.size[1]):
                color = Color(f'rgb({random_short()},{random_short()},{random_short()}')
                draw.fill_color = color
                draw.point(x, y)
            draw(image)
    image.save(filename=filename)


def save(image: Image, filename: str) -> None:
    """
    Save imqge without letting the wand module create a backup file (which would
    confuse tearDownClass()
    """
    with open(filename, 'wb') as f:
        image.save(file=f)


class SetupImages(unittest.TestCase):

    width = 100
    ASPECT_FUZZINESS = 0.05
    RMS_ERROR = 0.05

    top_directory = ''
    sub_directory = ''
    image_files = []  # type: List[str]
    jpeg_file = ''
    png_file = ''
    half_file = ''
    subdir_file = ''

    @classmethod
    def setUpClass(cls) -> None:
        """create a number of image files in a tree structure under /tmp"""
        cls.top_directory = tempfile.mkdtemp(dir="/tmp")
        cls.image_files = []
        cls.jpeg_file = create_image(
            tempfile.mkstemp(dir=cls.top_directory, prefix="jpeg_", suffix=".jpg")[1], cls.width
        )
        cls.image_files.append(cls.jpeg_file)
        cls.png_file = create_image(
            tempfile.mkstemp(dir=cls.top_directory, prefix="png_", suffix=".png")[1], cls.width
        )
        cls.image_files.append(cls.png_file)
        cls.sub_directory = tempfile.mkdtemp(dir=cls.top_directory)
        cls.subdir_file = create_image(
            tempfile.mkstemp(dir=cls.sub_directory, prefix="subdir_", suffix=".jpg")[1], cls.width
        )
        fill_image_with_random_pixels(cls.subdir_file)
        cls.image_files.append(cls.subdir_file)
        cls.half_file = create_image(
            tempfile.mkstemp(dir=cls.top_directory, prefix="test_half_", suffix=".jpg")[1],
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
            os.remove(file)
        os.rmdir(cls.sub_directory)
        os.rmdir(cls.top_directory)

    def get_image_files(self) -> List[str]:
        return sorted(duplicate.files_in_dirs([self.top_directory]))
