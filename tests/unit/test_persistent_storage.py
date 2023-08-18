__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import json
import pickle
import tempfile
from itertools import combinations
from pathlib import Path
from typing import Optional
from unittest.mock import Mock

import pytest
from imagehash import ImageHash
from numpy import array

from duplicate_images.function_types import Cache
from duplicate_images.image_pair_finder import SerialImagePairFinder
from duplicate_images.hash_store import PickleHashStore
from tests.unit.setup_images import SetupImages


def check_flaky_condition(condition: bool) -> None:
    if not condition:
        pytest.skip('flaky test failed, ignoring')
    assert condition


class TestPersistentStorage(SetupImages):

    MOCK_IMAGE_HASH_VALUE = ImageHash(array([[True, True], [True, True]]))  # just some random value
    MOCK_ALGORITHM = Mock(return_value=MOCK_IMAGE_HASH_VALUE)

    def setUp(self) -> None:
        super().setUp()
        self.equal_images = [self.jpeg_file, self.png_file, self.half_file]
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
        hash_store_path = self.get_hash_store_path('.pickle')
        self.create_verified_hash_store(hash_store_path)
        assert hash_store_path.is_file()

    def test_json_file_is_written(self) -> None:
        hash_store_path = self.get_hash_store_path('.json')
        self.create_verified_hash_store(hash_store_path)
        assert hash_store_path.is_file()

    def test_pickle_file_contains_correct_hashes(self) -> None:
        hash_store_path = self.get_hash_store_path('.pickle')
        self.create_verified_hash_store(hash_store_path)
        with hash_store_path.open('rb') as pickle_file:
            written_hashes = pickle.load(pickle_file)
        for file_name in self.equal_images:
            assert file_name in written_hashes
            assert written_hashes[file_name] == self.MOCK_IMAGE_HASH_VALUE

    def test_json_file_contains_correct_hashes(self) -> None:
        hash_store_path = self.get_hash_store_path('.json')
        self.create_verified_hash_store(hash_store_path)
        with hash_store_path.open('rb') as pickle_file:
            written_hashes = json.load(pickle_file)
        for file_name in self.equal_images:
            assert str(file_name) in written_hashes
            assert written_hashes[str(file_name)] == str(self.MOCK_IMAGE_HASH_VALUE)

    def test_backup_pickle_file_created(self) -> None:
        hash_store_path = self.get_hash_store_path('.pickle')
        self.create_verified_hash_store(hash_store_path)
        assert not hash_store_path.with_suffix('.bak').is_file()
        self.create_verified_hash_store(hash_store_path)
        assert hash_store_path.with_suffix('.bak').is_file()

    def test_backup_json_file_created(self) -> None:
        hash_store_path = self.get_hash_store_path('.json')
        self.create_verified_hash_store(hash_store_path)
        assert not hash_store_path.with_suffix('.bak').is_file()
        self.create_verified_hash_store(hash_store_path)
        assert hash_store_path.with_suffix('.bak').is_file()

    def test_existing_pickle_backup_file_does_not_lead_to_error(self) -> None:
        hash_store_path = self.get_hash_store_path('.pickle')
        self.create_verified_hash_store(hash_store_path)
        self.create_verified_hash_store(hash_store_path)
        self.create_verified_hash_store(hash_store_path)

    def test_existing_json_backup_file_does_not_lead_to_error(self) -> None:
        hash_store_path = self.get_hash_store_path('.json')
        self.create_verified_hash_store(hash_store_path)
        self.create_verified_hash_store(hash_store_path)
        self.create_verified_hash_store(hash_store_path)

    @staticmethod
    def get_hash_store_path(suffix: str) -> Path:
        top_directory = Path(tempfile.mkdtemp())
        return Path(tempfile.NamedTemporaryFile(dir=top_directory, suffix=suffix).name)

    def generate_correct_hashes(self, finder: SerialImagePairFinder) -> None:
        finder.precalculate_hashes(self.get_image_files())
        self.check_correct_results(finder)

    def create_verified_hash_store(self, hash_store_path: Path) -> None:
        with PickleHashStore.create(hash_store_path) as hash_store:
            finder = self.create_pair_finder(hash_store)
            self.generate_correct_hashes(finder)

    def create_pair_finder(self, hash_store: Optional[Cache]) -> SerialImagePairFinder:
        return SerialImagePairFinder(
            self.get_image_files(), self.MOCK_ALGORITHM, hash_store=hash_store
        )

    def check_correct_results(self, finder: SerialImagePairFinder) -> None:
        pairs = finder.get_pairs()
        expected_pairs = combinations(self.equal_images, 2)
        expected_pairs_string = f'{[(p[0].name, p[1].name) for p in pairs]}'
        for pair in expected_pairs:
            assert pair in pairs, f'{pair[0].name}, {pair[1].name} not in {expected_pairs_string}'
