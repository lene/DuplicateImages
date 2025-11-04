# pylint: disable=missing-docstring
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import json
import logging
import pickle
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from typing import List

import pytest

from duplicate_images.duplicate import files_in_dirs, is_image_file
from duplicate_images.function_types import Cache
from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.pair_finder_options import PairFinderOptions
from duplicate_images.hash_store import (
    PickleHashStore, JSONHashStore, FileHashStore, HashStore, NullHashStore
)
from .conftest import MOCK_IMAGE_HASH_VALUE, mock_algorithm, create_jpg_and_png

DEFAULT_ALGORITHM = 'phash'
DEFAULT_HASH_SIZE = {'hash_size': 8}
DEFAULT_METADATA = {'algorithm': DEFAULT_ALGORITHM, **DEFAULT_HASH_SIZE}


class MockHashStore(FileHashStore):  # pylint: disable=abstract-method
    def __init__(self, values: Cache) -> None:  # pylint: disable=super-init-not-called
        self.values = values


@pytest.mark.skip(reason="HEIF support broken in 0.11.9 - test fails for unrelated reason")
def test_empty_hash_store_calculates_hash_values(
        top_directory: TemporaryDirectory, image_files: List[Path],
        reset_call_count  # pylint: disable=unused-argument
) -> None:
    finder = generate_pair_finder(top_directory, NullHashStore())
    assert mock_algorithm.call_count > 0
    check_correct_results(finder, image_files)


def test_filled_hash_store_does_not_calculate_hash_values(
        top_directory: TemporaryDirectory, image_files: List[Path],
        reset_call_count  # pylint: disable=unused-argument
) -> None:
    hash_store = MockHashStore({path: MOCK_IMAGE_HASH_VALUE for path in image_files})
    generate_pair_finder(top_directory, hash_store)
    assert mock_algorithm.call_count == 0


def test_empty_hash_store_is_filled(
        top_directory: TemporaryDirectory, reset_call_count  # pylint: disable=unused-argument
) -> None:
    finder = generate_pair_finder(top_directory, NullHashStore())
    original_call_number = mock_algorithm.call_count
    finder.get_equal_groups()
    assert mock_algorithm.call_count == original_call_number


@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_hash_store_is_written(
        top_directory: TemporaryDirectory, hash_store_path: Path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    assert hash_store_path.is_file()


@pytest.mark.skip(reason="HEIF support broken in 0.11.9 - test fails for unrelated reason")
@pytest.mark.parametrize('file_type', ['pickle'])
def test_pickle_file_contains_correct_hashes(
        top_directory: TemporaryDirectory, image_files: List[Path], hash_store_path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    with hash_store_path.open('rb') as pickle_file:
        written_hashes = pickle.load(pickle_file)[0]
    for file_name in image_files:
        assert file_name in written_hashes
        assert written_hashes[file_name] == MOCK_IMAGE_HASH_VALUE


@pytest.mark.skip(reason="HEIF support broken in 0.11.9 - test fails for unrelated reason")
@pytest.mark.parametrize('file_type', ['json'])
def test_json_file_contains_correct_hashes(
        top_directory: TemporaryDirectory, image_files: List[Path], hash_store_path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    with hash_store_path.open('r') as json_file:
        written_hashes = json.load(json_file)[0]
    for file_name in image_files:
        assert str(file_name) in written_hashes
        assert written_hashes[str(file_name)] == str(MOCK_IMAGE_HASH_VALUE)


@pytest.mark.skip(reason="HEIF support broken in 0.11.9 - test fails for unrelated reason")
@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_hash_store_load_loads(
        top_directory: TemporaryDirectory, image_files: List[Path], hash_store_path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    hash_store_class = PickleHashStore if hash_store_path.suffix == '.pickle' else JSONHashStore
    hash_store = hash_store_class(hash_store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
    hash_store.load()
    written_hashes = hash_store.values
    for file_name in image_files:
        assert str(file_name) in map(str, written_hashes.keys())
        assert str(written_hashes[file_name]) == str(MOCK_IMAGE_HASH_VALUE)


@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_backup_file_created(
        top_directory: TemporaryDirectory, hash_store_path: Path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    assert not hash_store_path.with_suffix('.bak').is_file()
    create_verified_hash_store(top_directory, hash_store_path)
    assert hash_store_path.with_suffix('.bak').is_file()


@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_existing_backup_file_does_not_lead_to_error(
        top_directory: TemporaryDirectory, hash_store_path: Path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)  # create hash store
    create_verified_hash_store(top_directory, hash_store_path)  # create backup file
    create_verified_hash_store(top_directory, hash_store_path)  # check it works still


@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_checked_load_sets_values(top_directory: TemporaryDirectory, hash_store_path: Path) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    hash_store_class = PickleHashStore if hash_store_path.suffix == '.pickle' else JSONHashStore
    hash_store = hash_store_class(hash_store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
    hash_store.load()
    logging.warning(image_list(top_directory))
    assert hash_store.values == {path: MOCK_IMAGE_HASH_VALUE for path in image_list(top_directory)}


@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_checked_load_sets_metadata(
        top_directory: TemporaryDirectory, hash_store_path: Path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    hash_store_class = PickleHashStore if hash_store_path.suffix == '.pickle' else JSONHashStore
    hash_store = hash_store_class(hash_store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
    hash_store.load()
    assert hash_store.metadata() == DEFAULT_METADATA


@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_hash_store_not_written_if_not_changed(
        top_directory: TemporaryDirectory, hash_store_path: Path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    assert hash_store_path.is_file()
    creation_time = hash_store_path.stat().st_ctime
    scan_images_with_hash_store(top_directory, hash_store_path)
    assert hash_store_path.stat().st_ctime == creation_time
    assert hash_store_path.stat().st_mtime == creation_time


@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_hash_store_is_accessed_even_if_not_changed(
        top_directory: TemporaryDirectory, hash_store_path: Path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    assert hash_store_path.is_file()
    sleep(0.01)  # ensure the access time is different
    creation_time = hash_store_path.stat().st_ctime
    scan_images_with_hash_store(top_directory, hash_store_path)
    assert hash_store_path.stat().st_atime > creation_time


def image_list(top_directory: TemporaryDirectory) -> List[Path]:
    return sorted(files_in_dirs([top_directory.name], is_relevant=is_image_file))


def generate_pair_finder(
        top_directory: TemporaryDirectory, hash_store: HashStore
) -> ImagePairFinder:
    return ImagePairFinder.create(
        image_list(top_directory), mock_algorithm, options=PairFinderOptions(slow=True),
        hash_store=hash_store
    )


def create_verified_hash_store(top_directory: TemporaryDirectory, store_path: Path) -> None:
    create_jpg_and_png(top_directory)
    scan_images_with_hash_store(top_directory, store_path)


def scan_images_with_hash_store(top_directory: TemporaryDirectory, store_path: Path) -> None:
    with FileHashStore.create(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as hash_store:
        finder = generate_pair_finder(top_directory, hash_store)
        finder.get_equal_groups()


def check_correct_results(finder: ImagePairFinder, images: List[Path]) -> None:
    pairs = finder.get_equal_groups()
    expected_pairs = combinations(images, 2)
    expected_pairs_string = f'{[(p[0].name, p[1].name) for p in pairs]}'
    for pair in expected_pairs:
        assert pair in pairs or (pair[1], pair[0]) in pairs, \
            f'{pair[0].name}, {pair[1].name} not in {expected_pairs_string}'
