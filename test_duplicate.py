__author__ = 'lene'

import unittest
import tempfile
import os
import shutil
import random
import PythonMagick

import duplicate


def create_image(filename, width):
    geometry = PythonMagick.Geometry(int(width), int(width*3/4))
    color = PythonMagick.Color("Black")
    image = PythonMagick.Image(geometry, color)
    image.write(filename)
    return filename


def random_short():
    return random.randrange(65535)


def fill_image_with_random_pixels(filename):
    random.seed(0)
    image = PythonMagick.Image(filename)
    for x in range(0, image.size().width()):
        for y in range(0, image.size().height()):
            color = PythonMagick.Color(random_short(), random_short(), random_short())
            image.pixelColor(x, y, color)
    image.write(filename)


def display_image(filename):
    image = PythonMagick.Image(filename)
    image.display(image)


def element_in_list_of_tuples(element, tuples):
    return any(element in tuple for tuple in tuples)


class DuplicateTest(unittest.TestCase):

    width = 400

    @classmethod
    def setUpClass(cls):
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
            tempfile.mkstemp(dir=cls.top_directory, prefix="test_half_", suffix=".jpg")[1], cls.width
        )
        image = PythonMagick.Image(cls.half_file)
        image.transform('{}x{}'.format(int(cls.width / 2), int(cls.width * 3 / 8)))
        image.write(cls.half_file)
        cls.image_files.append(cls.half_file)

    @classmethod
    def tearDownClass(cls):
        """"remove all the files created by setUp"""
        for file in cls.image_files:
            os.remove(file)
        os.rmdir(cls.sub_directory)
        os.rmdir(cls.top_directory)

    def testGetFiles(self):
        files = duplicate.files_in_dir(self.top_directory)
        assert set(files) == set(self.image_files)

    def testEqualFilesFindsNothingThatIsNotThere(self):
        equals = duplicate.similar_images(self.get_image_files(), duplicate.compare_exactly)
        assert len(equals) == 0

    def testEqualFilesFindsCopiedFile(self):
        copied_file = self.copy_image_file(self.jpeg_file)
        equals = duplicate.similar_images(self.get_image_files(), duplicate.compare_exactly)
        assert len(equals) == 1
        assert equals.count((self.jpeg_file, copied_file)) == 1
        self.delete_image_file(copied_file)

    def testHistogramsEqualForCopiedImage(self):
        copied_file = self.copy_image_file(self.jpeg_file)
        equals = duplicate.similar_images(self.get_image_files(), duplicate.compare_histograms)
        assert (self.jpeg_file, copied_file) in equals
        self.delete_image_file(copied_file)

    def testHistogramsNotEqualForNoisyImage(self):
        equals = duplicate.similar_images(self.get_image_files(), duplicate.compare_histograms)
        assert not element_in_list_of_tuples(self.subdir_file, equals)

    def testHistogramsEqualForDifferentImageFormat(self):
        equals = duplicate.similar_images(self.get_image_files(), duplicate.compare_histograms)
        assert (self.jpeg_file, self.png_file) in equals

    def testHistogramsEqualForScaledImage(self):
        equals = duplicate.similar_images(self.get_image_files(), duplicate.compare_histograms)
        assert (self.jpeg_file, self.half_file) in equals

    def get_image_files(self):
        return sorted(duplicate.files_in_dir(self.top_directory))

    def copy_image_file(self, filename):
        copied_file = filename + ".bak"
        shutil.copyfile(filename, copied_file)
        self.image_files.append(copied_file)
        return copied_file

    def delete_image_file(self, filename):
        os.remove(filename)
        self.image_files.remove(filename)


if __name__ == '__main__':
    from sys import argv

    if len(argv) > 1:
        DuplicateTest.width = int(argv[1])

    suite = unittest.TestSuite()
    suite.addTest(DuplicateTest("testGetFiles"))
    suite.addTest(DuplicateTest("testEqualFilesFindsNothingThatIsNotThere"))
    suite.addTest(DuplicateTest("testEqualFilesFindsCopiedFile"))
    suite.addTest(DuplicateTest("testHistogramsEqualForCopiedImage"))
    suite.addTest(DuplicateTest("testHistogramsNotEqualForNoisyImage"))
    suite.addTest(DuplicateTest("testHistogramsEqualForDifferentImageFormat"))
    suite.addTest(DuplicateTest("testHistogramsEqualForScaledImage"))

    unittest.TextTestRunner().run(suite)
