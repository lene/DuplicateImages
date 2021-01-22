__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import pickle
import tempfile
from itertools import combinations
from pathlib import Path
from unittest.mock import Mock

from duplicate_images.cache_decorator import CacheDecorator
from duplicate_images.create_pair_finder import create_pair_finder
from duplicate_images.methods import IMAGE_HASH_ALGORITHM
from duplicate_images.pair_finder_interface import PairFinderInterface
from duplicate_images.hash_store import PickleHashStore
from tests.setup_images import SetupImages


class TestPersistentStorage(SetupImages):

    MOCK_IMAGE_HASH_VALUE = 123  # just some random value
    MOCK_ALGORITHM = Mock(return_value=MOCK_IMAGE_HASH_VALUE)

    def setUp(self) -> None:
        super().setUp()
        self.equal_images = [self.jpeg_file, self.png_file, self.half_file, self.subdir_file]

    def test_empty_hash_store_is_filled(self) -> None:
        finder = create_pair_finder(
            self.get_image_files(), IMAGE_HASH_ALGORITHM['ahash'], self.options, hash_store=None
        )
        assert isinstance(finder, PairFinderInterface)
        assert not isinstance(finder, CacheDecorator)

    def test_empty_hash_store_recalculates_hash_values(self) -> None:
        finder = create_pair_finder(
            self.get_image_files(), self.MOCK_ALGORITHM, self.options, hash_store=None
        )
        assert not isinstance(finder, CacheDecorator)
        finder.calculate_hashes()
        self.check_correct_results(finder)
        assert self.MOCK_ALGORITHM.call_count > 0

    def test_filled_hash_store_does_not_calculate_hash_values(self) -> None:
        hash_store = {path: self.MOCK_IMAGE_HASH_VALUE for path in self.get_image_files()}
        finder = create_pair_finder(
            self.get_image_files(), self.MOCK_ALGORITHM, self.options, hash_store=hash_store
        )
        assert isinstance(finder, CacheDecorator)
        finder.calculate_hashes()
        self.check_correct_results(finder)
        assert self.MOCK_ALGORITHM.call_count == 0

    def test_pickle_file_is_written(self) -> None:
        top_directory = Path(tempfile.mkdtemp())
        hash_store_path = Path(tempfile.mkstemp(dir=top_directory, suffix=".pickle")[1])
        with PickleHashStore.create(hash_store_path) as hash_store:
            finder = create_pair_finder(
                self.get_image_files(), self.MOCK_ALGORITHM, self.options, hash_store=hash_store
            )
            finder.calculate_hashes()
            self.check_correct_results(finder)
        assert hash_store_path.is_file()
        with hash_store_path.open('rb') as pickle_file:
            written_hashes = pickle.load(pickle_file)
        for file_name in self.equal_images:
            assert file_name in written_hashes
            assert written_hashes[file_name] == self.MOCK_IMAGE_HASH_VALUE

    def check_correct_results(self, finder: PairFinderInterface) -> None:
        pairs = finder.get_pairs()
        for pair in combinations(self.equal_images, 2):
            assert pair in pairs
