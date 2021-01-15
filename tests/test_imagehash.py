from duplicate_images import duplicate
from duplicate_images.methods import COMPARISON_METHODS

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

    def execute_for_hash(self, hash_func: str) -> None:
        equals = duplicate.similar_images(
            self.get_image_files(), COMPARISON_METHODS[hash_func], self.ASPECT_FUZZINESS,
            self.RMS_ERROR
        )
        assert (self.jpeg_file, self.half_file) in equals
        assert (self.jpeg_file, self.png_file) in equals
        assert (self.jpeg_file, self.subdir_file) not in equals
