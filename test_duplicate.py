__author__ = 'lene'

import unittest
import tempfile
import os
import shutil
import random
import PythonMagick
import PIL
from math import sqrt

import duplicate

def createImage(filename):
    geometry = PythonMagick.Geometry(createImage.width, createImage.width*3/4)
    color = PythonMagick.Color("Black")
    image = PythonMagick.Image(geometry, color)
    image.write(filename)
    return filename

def randomShort(): return random.randrange(65535)

def fillImageWithRandomPixels(filename):
    image = PythonMagick.Image(filename)
    for x in range(0, image.size().width()):
        for y in range(0, image.size().height()):
            color = PythonMagick.Color(randomShort(), randomShort(), randomShort())
            image.pixelColor(x, y, color)
    image.write(filename)

def displayImage(filename):
    image = PythonMagick.Image(filename)
    image.display()

def elementInListOfTuples(element, list):
    for tuple in list:
        for scalar in tuple:
            if scalar == element: return True
    return False


class DuplicateTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        "create a number of image files in a tree structure under /tmp"
        cls.top_directory = tempfile.mkdtemp(dir="/tmp")
        cls.image_files = []
        cls.jpeg_file = createImage(tempfile.mkstemp(dir=cls.top_directory, prefix="jpeg_", suffix=".jpg")[1])
        cls.image_files.append(cls.jpeg_file)
        cls.png_file = createImage(tempfile.mkstemp(dir=cls.top_directory, prefix="png_", suffix=".png")[1])
        cls.image_files.append(cls.png_file)
        cls.sub_directory = tempfile.mkdtemp(dir=cls.top_directory)
        cls.subdir_file = createImage(tempfile.mkstemp(dir=cls.sub_directory, prefix="subdir_", suffix=".jpg")[1])
        fillImageWithRandomPixels(cls.subdir_file)
        cls.image_files.append(cls.subdir_file)

    @classmethod
    def tearDownClass(cls):
        "remove all the files created by setUp"
        for file in cls.image_files: os.remove(file)
        os.rmdir(cls.sub_directory)
        os.rmdir(cls.top_directory)

    def testGetFiles(self):
        files = duplicate.filesInDir(self.top_directory)
        assert set(files) == set(self.image_files)


    def testEqualFiles(self):
        copied_file = self.copyImageFile(self.jpeg_file)
        equals = duplicate.compareForEquality(self.getImageFiles(), duplicate.compareExactly)
        assert len(equals) == 1
        assert equals.count((self.jpeg_file, copied_file)) == 1
        self.deleteImageFile(copied_file)


    def testHistograms(self):
        copied_file = self.copyImageFile(self.jpeg_file)
        equals = duplicate.compareForEquality(self.getImageFiles(), duplicate.compareHistograms)
        assert (self.jpeg_file, copied_file) in equals
#        assert (self.jpeg_file, self.png_file) in equals
        assert not elementInListOfTuples(self.subdir_file, equals)
        self.deleteImageFile(copied_file)

    def getImageFiles(self): return sorted(duplicate.filesInDir(self.top_directory))

    def copyImageFile(self, filename):
        copied_file = filename + ".bak"
        shutil.copyfile(filename, copied_file)
        self.image_files.append(copied_file)
        return copied_file

    def deleteImageFile(self, filename):
        os.remove(filename)
        self.image_files.remove(filename)


if __name__ == '__main__':
    from sys import argv

    createImage.width = int(argv[1]) if len(argv) > 1 else 200

    suite = unittest.TestSuite()
    suite.addTest(DuplicateTest("testGetFiles"))
    suite.addTest(DuplicateTest("testEqualFiles"))
    suite.addTest(DuplicateTest("testHistograms"))

    unittest.TextTestRunner().run(suite)
