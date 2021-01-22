from duplicate_images.function_types import Results
from duplicate_images.image_pair_finder import ImagePairFinder, ParallelImagePairFinder
from duplicate_images.methods import IMAGE_HASH_ALGORITHM
from duplicate_images.parallel_options import ParallelOptions

from tests.setup_images import SetupImages


class TestImageHash(SetupImages):

    def test_ahash(self) -> None:
        self.execute_for_hash('ahash')

    def test_dhash(self) -> None:
        self.execute_for_hash('dhash')

    def test_colorhash(self) -> None:
        self.execute_for_hash('colorhash')

    def test_phash(self) -> None:
        self.execute_for_hash('phash')

    def test_whash(self) -> None:
        self.execute_for_hash('whash')

    def test_ahash_parallel(self) -> None:
        self.execute_parallel_for_hash('ahash')

    def test_dhash_parallel(self) -> None:
        self.execute_parallel_for_hash('dhash')

    def test_colorhash_parallel(self) -> None:
        self.execute_parallel_for_hash('colorhash')

    def test_phash_parallel(self) -> None:
        self.execute_parallel_for_hash('phash')

    def test_whash_parallel(self) -> None:
        self.execute_parallel_for_hash('whash')

    def execute_for_hash(self, hash_func: str) -> None:
        finder = ImagePairFinder(
            self.get_image_files(), IMAGE_HASH_ALGORITHM[hash_func]
        )
        finder.calculate_hashes()
        equals = finder.get_pairs()
        self.check_results(equals)

    def execute_parallel_for_hash(self, hash_func: str) -> None:
        finder = ParallelImagePairFinder(
            self.get_image_files(), IMAGE_HASH_ALGORITHM[hash_func],
            ParallelOptions(parallel=True)
        )
        finder.calculate_hashes()
        equals = finder.get_pairs()
        self.check_results(equals)

    def check_results(self, equals: Results) -> None:
        assert (self.jpeg_file, self.half_file) in equals
        assert (self.jpeg_file, self.png_file) in equals
        assert (self.jpeg_file, self.subdir_file) not in equals
