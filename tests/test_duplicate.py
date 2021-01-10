__author__ = 'lene'

import unittest
import tempfile
import os
import shutil
import random
from typing import Any, List, Tuple

from wand.color import Color
from wand.display import display
from wand.drawing import Drawing
from wand.image import Image

from duplicate_images import duplicate
from duplicate_images.image_hash import resize
from duplicate_images.image_wrapper import ImageWrapper
from duplicate_images.methods import compare_histograms, compare_exactly, compare_image_hash


def save(image: Image, filename: str) -> None:
    """
    Save imqge without letting the wand module create a backup file (which would
    confuse tearDownClass()
    """
    with open(filename, 'wb') as f:
        image.save(file=f)


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


def display_image(filename: str) -> None:
    image = Image(filename=filename)
    display(image)


def element_in_list_of_tuples(element: Any, tuples: List[Tuple[Any, Any]]) -> bool:
    return any(element in tuple for tuple in tuples)


class DuplicateTest(unittest.TestCase):

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

    def testGetFiles(self) -> None:
        files = duplicate.files_in_dirs([self.top_directory])
        assert set(files) == set(self.image_files)

    def testEqualFilesFindsNothingThatIsNotThere(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_exactly, self.ASPECT_FUZZINESS, self.RMS_ERROR
        )
        assert len(equals) == 0

    def testEqualFilesFindsCopiedFile(self) -> None:
        copied_file = self.copy_image_file(self.jpeg_file)
        equals = duplicate.similar_images(
            self.get_image_files(), compare_exactly, self.ASPECT_FUZZINESS, self.RMS_ERROR
        )
        try:
            assert len(equals) == 1
            assert equals.count((self.jpeg_file, copied_file)) == 1
        finally:
            self.delete_image_file(copied_file)

    def testHistogramsEqualForCopiedImage(self) -> None:
        copied_file = self.copy_image_file(self.jpeg_file)
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.ASPECT_FUZZINESS,
            self.RMS_ERROR
        )
        try:
            assert (self.jpeg_file, copied_file) in equals
        finally:
            self.delete_image_file(copied_file)

    def testHistogramsNotEqualForNoisyImage(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.ASPECT_FUZZINESS,
            self.RMS_ERROR
        )
        assert not element_in_list_of_tuples(self.subdir_file, equals)

    def testHistogramsEqualForDifferentImageFormat(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.ASPECT_FUZZINESS,
            self.RMS_ERROR
        )
        assert (self.jpeg_file, self.png_file) in equals

    def testHistogramsEqualForScaledImage(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.ASPECT_FUZZINESS,
            self.RMS_ERROR
        )
        assert (self.jpeg_file, self.half_file) in equals

    def test_resize(self):
        for image_file in duplicate.files_in_dirs([self.top_directory]):
            resized = resize(ImageWrapper.create(image_file))
            assert resized.image.width == 200

    def test_image_hashes(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_image_hash, self.ASPECT_FUZZINESS,
            self.RMS_ERROR
        )
        assert (self.jpeg_file, self.half_file) in equals
        assert (self.jpeg_file, self.png_file) in equals

    def testParallelFilteringGivesSameResults(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.ASPECT_FUZZINESS,
            self.RMS_ERROR, parallel=True
        )
        assert not element_in_list_of_tuples(self.subdir_file, equals)
        assert (self.jpeg_file, self.png_file) in equals
        assert (self.jpeg_file, self.half_file) in equals

    def get_image_files(self) -> List[str]:
        return sorted(duplicate.files_in_dirs([self.top_directory]))

    def copy_image_file(self, filename: str) -> str:
        copied_file = filename + ".bak"
        shutil.copyfile(filename, copied_file)
        self.image_files.append(copied_file)
        return copied_file

    def delete_image_file(self, filename: str) -> None:
        os.remove(filename)
        self.image_files.remove(filename)
