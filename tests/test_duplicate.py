__author__ = 'lene'

import os
import shutil
from typing import Any, List, Tuple

from wand.display import display
from wand.image import Image

from duplicate_images import duplicate
from duplicate_images.methods import compare_histograms, compare_exactly
from tests.setup_images import SetupImages


def display_image(filename: str) -> None:
    image = Image(filename=filename)
    display(image)


def element_in_list_of_tuples(element: Any, tuples: List[Tuple[Any, Any]]) -> bool:
    return any(element in tuple for tuple in tuples)


class DuplicateTest(SetupImages):

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

    def testParallelFilteringGivesSameResults(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.ASPECT_FUZZINESS,
            self.RMS_ERROR, parallel=True
        )
        assert not element_in_list_of_tuples(self.subdir_file, equals)
        assert (self.jpeg_file, self.png_file) in equals
        assert (self.jpeg_file, self.half_file) in equals

    def copy_image_file(self, filename: str) -> str:
        copied_file = filename + ".bak"
        shutil.copyfile(filename, copied_file)
        self.image_files.append(copied_file)
        return copied_file

    def delete_image_file(self, filename: str) -> None:
        os.remove(filename)
        self.image_files.remove(filename)
