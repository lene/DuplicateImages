__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import pickle
import tempfile
from itertools import combinations
from pathlib import Path
from typing import Optional
from unittest.mock import Mock

from duplicate_images.function_types import Cache
from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.hash_store import PickleHashStore
from tests.unit.setup_images import SetupImages


class TestPersistentStorage(SetupImages):

    MOCK_IMAGE_HASH_VALUE = 123  # just some random value
    MOCK_ALGORITHM = Mock(return_value=MOCK_IMAGE_HASH_VALUE)

    def setUp(self) -> None:
        super().setUp()
        self.equal_images = [self.jpeg_file, self.png_file, self.half_file, self.subdir_file]
        self.MOCK_ALGORITHM.call_count = 0

    def test_empty_hash_store_recalculates_hash_values(self) -> None:
        finder = self.create_pair_finder(None)
        self.generate_correct_hashes(finder)
        assert self.MOCK_ALGORITHM.call_count > 0

    def test_filled_hash_store_does_not_calculate_hash_values(self) -> None:
        hash_store = {path: self.MOCK_IMAGE_HASH_VALUE for path in self.get_image_files()}
        finder = self.create_pair_finder(hash_store)
        self.generate_correct_hashes(finder)
        assert self.MOCK_ALGORITHM.call_count == 0

    def test_empty_hash_store_is_filled(self) -> None:
        finder = self.create_pair_finder(None)
        self.generate_correct_hashes(finder)
        original_call_number = self.MOCK_ALGORITHM.call_count
        self.generate_correct_hashes(finder)
        assert self.MOCK_ALGORITHM.call_count == original_call_number

    def test_pickle_file_is_written(self) -> None:
        hash_store_path = self.get_hash_store_path()
        self.create_verified_hash_store(hash_store_path)
        assert hash_store_path.is_file()

    def test_pickle_file_contains_correct_hashes(self) -> None:
        hash_store_path = self.get_hash_store_path()
        self.create_verified_hash_store(hash_store_path)
        with hash_store_path.open('rb') as pickle_file:
            written_hashes = pickle.load(pickle_file)
        for file_name in self.equal_images:
            assert file_name in written_hashes
            assert written_hashes[file_name] == self.MOCK_IMAGE_HASH_VALUE

    @staticmethod
    def get_hash_store_path() -> Path:
        top_directory = Path(tempfile.mkdtemp())
        return Path(tempfile.mkstemp(dir=top_directory, suffix='.pickle')[1])

    def generate_correct_hashes(self, finder: ImagePairFinder) -> None:
        finder.precalculate_hashes(self.get_image_files())
        self.check_correct_results(finder)

    def create_verified_hash_store(self, hash_store_path: Path) -> None:
        with PickleHashStore.create(hash_store_path) as hash_store:
            finder = self.create_pair_finder(hash_store)
            self.generate_correct_hashes(finder)

    def create_pair_finder(self, hash_store: Optional[Cache]) -> ImagePairFinder:
        return ImagePairFinder.create(
            self.get_image_files(), self.MOCK_ALGORITHM, hash_store=hash_store
        )

    def check_correct_results(self, finder: ImagePairFinder) -> None:
        pairs = finder.get_pairs()
        for pair in combinations(self.equal_images, 2):
            assert pair in pairs
