__author__ = 'lene'

import unittest
import tempfile
import os
import shutil
import PythonMagick

import duplicate

def createImage(filename):
    geometry = PythonMagick.Geometry(200,150)
    color = PythonMagick.Color()
    image = PythonMagick.Image(geometry, color)
    image.write(filename)
    return filename

def fillImageWithRandomPixels(filename):
    image = PythonMagick.Image(filename)
    for x in range(0, image.size().width()):
        for y in range(0, image.size().height()):
            image.pixelColor(x, y, "Red")
    image.write(filename)

class DuplicateTest(unittest.TestCase):

    def setUp(self):
        "create a number of image files in a tree structure under /tmp"
        self.top_directory = tempfile.mkdtemp(dir="/tmp")
        self.image_files = []
        self.jpeg_file = createImage(tempfile.mkstemp(dir=self.top_directory, suffix=".jpg")[1])
        self.image_files.append(self.jpeg_file)
        self.png_file = createImage(tempfile.mkstemp(dir=self.top_directory, suffix=".png")[1])
        self.image_files.append(self.png_file)
        self.sub_directory = tempfile.mkdtemp(dir=self.top_directory)
        subdir_file = createImage(tempfile.mkstemp(dir=self.sub_directory, suffix=".jpg")[1])
        fillImageWithRandomPixels(subdir_file)
        self.image_files.append(subdir_file)

    def tearDown(self):
        "remove all the files created by setUp"
        for file in self.image_files: os.remove(file)
        os.rmdir(self.sub_directory)
        os.rmdir(self.top_directory)

    def testGetFiles(self):
        files = duplicate.filesInDir(self.top_directory)
        assert set(files) == set(self.image_files)

    def testEqualFiles(self):
        copied_file = self.jpeg_file+".bak"
        shutil.copyfile(self.jpeg_file, copied_file)
        self.image_files.append(copied_file)
        equals = (duplicate.compareForEquality(sorted(duplicate.filesInDir(self.top_directory)), duplicate.compareExactly))
        assert len(equals) == 1
        assert equals.count((self.jpeg_file, copied_file)) == 1


    def testHistograms(self):
        pass


if __name__ == '__main__':
    unittest.main()
