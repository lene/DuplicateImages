__author__ = 'lene'

from typing import Any, List, Tuple

from duplicate_images.duplicate import files_in_dirs
from duplicate_images.image_pair_finder import ImagePairFinder, ParallelImagePairFinder
from duplicate_images.parallel_options import ParallelOptions
from duplicate_images.methods import IMAGE_HASH_ALGORITHM
from tests.setup_images import SetupImages

HASH_ALGORITHM = IMAGE_HASH_ALGORITHM['phash']


def element_in_list_of_tuples(element: Any, tuples: List[Tuple[Any, Any]]) -> bool:
    return any(element in tuple for tuple in tuples)


class DuplicateTest(SetupImages):  # pylint: disable=too-many-public-methods

    def test_get_files(self) -> None:
        files = files_in_dirs([self.top_directory])
        assert set(files) == set(self.image_files)

    def test_hashes_equal_for_copied_image_ahash(self) -> None:
        self._check_hashes_equal_for_copied_image('ahash')

    def test_hashes_equal_for_copied_image_dhash(self) -> None:
        self._check_hashes_equal_for_copied_image('dhash')

    def test_hashes_equal_for_copied_image_colorhash(self) -> None:
        self._check_hashes_equal_for_copied_image('colorhash')

    def test_hashes_equal_for_copied_image_phash(self) -> None:
        self._check_hashes_equal_for_copied_image('phash')

    def test_hashes_equal_for_copied_image_whash(self) -> None:
        self._check_hashes_equal_for_copied_image('whash')

    def test_hashes_not_equal_for_noisy_image_ahash(self) -> None:
        self._check_hashes_not_equal_for_noisy_image('ahash')

    def test_hashes_not_equal_for_noisy_image_dhash(self) -> None:
        self._check_hashes_not_equal_for_noisy_image('dhash')

    def test_hashes_not_equal_for_noisy_image_colorhash(self) -> None:
        self._check_hashes_not_equal_for_noisy_image('colorhash')

    def test_hashes_not_equal_for_noisy_image_phash(self) -> None:
        self._check_hashes_not_equal_for_noisy_image('phash')

    def test_hashes_not_equal_for_noisy_image_whash(self) -> None:
        self._check_hashes_not_equal_for_noisy_image('whash')

    def test_hashes_equal_for_different_image_format_ahash(self) -> None:
        self._check_hashes_equal_for_different_image_format('ahash')

    def test_hashes_equal_for_different_image_format_dhash(self) -> None:
        self._check_hashes_equal_for_different_image_format('dhash')

    def test_hashes_equal_for_different_image_format_colorhash(self) -> None:
        self._check_hashes_equal_for_different_image_format('colorhash')

    def test_hashes_equal_for_different_image_format_phash(self) -> None:
        self._check_hashes_equal_for_different_image_format('phash')

    def test_hashes_equal_for_different_image_format_whash(self) -> None:
        self._check_hashes_equal_for_different_image_format('whash')

    def test_hashes_equal_for_scaled_image_ahash(self) -> None:
        self._check_hashes_equal_for_scaled_image('ahash')

    def test_hashes_equal_for_scaled_image_dhash(self) -> None:
        self._check_hashes_equal_for_scaled_image('dhash')

    def test_hashes_equal_for_scaled_image_colorhash(self) -> None:
        self._check_hashes_equal_for_scaled_image('colorhash')

    def test_hashes_equal_for_scaled_image_phash(self) -> None:
        self._check_hashes_equal_for_scaled_image('phash')

    def test_hashes_equal_for_scaled_image_whash(self) -> None:
        self._check_hashes_equal_for_scaled_image('whash')

    def test_parallel_filtering_gives_same_results_ahash(self) -> None:
        self._check_parallel_filtering_gives_same_results('ahash')

    def test_parallel_filtering_gives_same_results_dhash(self) -> None:
        self._check_parallel_filtering_gives_same_results('dhash')

    def test_parallel_filtering_gives_same_results_colorhash(self) -> None:
        self._check_parallel_filtering_gives_same_results('colorhash')

    def test_parallel_filtering_gives_same_results_phash(self) -> None:
        self._check_parallel_filtering_gives_same_results('phash')

    def test_parallel_filtering_gives_same_results_whash(self) -> None:
        self._check_parallel_filtering_gives_same_results('whash')

    def _check_hashes_equal_for_copied_image(self, algorithm: str) -> None:
        copied_file = self.copy_image_file(self.jpeg_file)
        finder = ImagePairFinder(
            self.get_image_files(), IMAGE_HASH_ALGORITHM[algorithm]
        )
        finder.calculate_hashes()
        equals = finder.get_pairs()
        try:
            assert self.is_pair_found(self.jpeg_file, copied_file, equals)
        finally:
            self.delete_image_file(copied_file)

    def _check_hashes_not_equal_for_noisy_image(self, algorithm: str) -> None:
        finder = ImagePairFinder(
            self.get_image_files(), IMAGE_HASH_ALGORITHM[algorithm]
        )
        finder.calculate_hashes()
        equals = finder.get_pairs()
        assert not element_in_list_of_tuples(self.subdir_file, equals)

    def _check_hashes_equal_for_different_image_format(self, algorithm: str) -> None:
        finder = ImagePairFinder(
            self.get_image_files(), IMAGE_HASH_ALGORITHM[algorithm]
        )
        finder.calculate_hashes()
        equals = finder.get_pairs()
        assert (self.jpeg_file, self.png_file) in equals

    def _check_hashes_equal_for_scaled_image(self, algorithm: str) -> None:
        finder = ImagePairFinder(
            self.get_image_files(), IMAGE_HASH_ALGORITHM[algorithm]
        )
        finder.calculate_hashes()
        equals = finder.get_pairs()
        assert (self.jpeg_file, self.half_file) in equals

    def _check_parallel_filtering_gives_same_results(self, algorithm: str) -> None:
        finder = ParallelImagePairFinder(
            self.get_image_files(), IMAGE_HASH_ALGORITHM[algorithm], ParallelOptions(parallel=True)
        )
        finder.calculate_hashes()
        equals = finder.get_pairs()
        assert len(equals) == 3
        assert self.is_pair_found(self.jpeg_file, self.png_file, equals)
        assert self.is_pair_found(self.jpeg_file, self.half_file, equals)
        assert self.is_pair_found(self.png_file, self.half_file, equals)
        assert not self.is_pair_found(self.jpeg_file, self.subdir_file, equals)
        assert not self.is_pair_found(self.png_file, self.subdir_file, equals)
        assert not self.is_pair_found(self.half_file, self.subdir_file, equals)
