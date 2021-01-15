__author__ = 'lene'

from typing import Any, List, Tuple

from duplicate_images import duplicate
from duplicate_images.duplicate import ParallelOptions
from duplicate_images.methods import compare_histograms, compare_exactly
from tests.setup_images import SetupImages


def element_in_list_of_tuples(element: Any, tuples: List[Tuple[Any, Any]]) -> bool:
    return any(element in tuple for tuple in tuples)


class DuplicateTest(SetupImages):

    def test_get_files(self) -> None:
        files = duplicate.files_in_dirs([self.top_directory])
        assert set(files) == set(self.image_files)

    def test_equal_files_finds_nothing_that_is_not_there(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_exactly, self.OPTIONS
        )
        assert len(equals) == 0

    def test_equal_files_finds_copied_file(self) -> None:
        copied_file = self.copy_image_file(self.jpeg_file)
        equals = duplicate.similar_images(
            self.get_image_files(), compare_exactly, self.OPTIONS
        )
        try:
            assert len(equals) == 1
            assert self.is_pair_found(self.jpeg_file, copied_file, equals)
        finally:
            self.delete_image_file(copied_file)

    def test_histograms_equal_for_copied_image(self) -> None:
        copied_file = self.copy_image_file(self.jpeg_file)
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.OPTIONS
        )
        try:
            assert self.is_pair_found(self.jpeg_file, copied_file, equals)
        finally:
            self.delete_image_file(copied_file)

    def test_histograms_not_equal_for_noisy_image(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.OPTIONS
        )
        assert not element_in_list_of_tuples(self.subdir_file, equals)

    def test_histograms_equal_for_different_image_format(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.OPTIONS
        )
        assert (self.jpeg_file, self.png_file) in equals

    def test_histograms_equal_for_scaled_image(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.OPTIONS
        )
        assert (self.jpeg_file, self.half_file) in equals

    def test_parallel_filtering_gives_same_results(self) -> None:
        copied_file = self.copy_image_file(self.jpeg_file)
        equals = duplicate.similar_images(
            self.get_image_files(), compare_exactly, self.OPTIONS, ParallelOptions(parallel=True)
        )
        try:
            assert len(equals) == 1
            assert self.is_pair_found(self.jpeg_file, copied_file, equals)
        finally:
            self.delete_image_file(copied_file)

    def test_parallel_filtering_gives_same_results_histogram(self) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), compare_histograms, self.OPTIONS, ParallelOptions(parallel=True)
        )
        assert not element_in_list_of_tuples(self.subdir_file, equals)
        assert (self.jpeg_file, self.png_file) in equals
        assert (self.jpeg_file, self.half_file) in equals
