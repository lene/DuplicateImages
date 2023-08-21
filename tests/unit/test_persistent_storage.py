__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import json
import pickle
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List

import pytest

from duplicate_images import duplicate
from duplicate_images.function_types import Cache
from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.pair_finder_options import PairFinderOptions
from duplicate_images.hash_store import PickleHashStore
from .conftest import MOCK_IMAGE_HASH_VALUE, mock_algorithm


def test_empty_hash_store_calculates_hash_values(
        top_directory: TemporaryDirectory, image_files: List[Path],
        reset_call_count  # pylint: disable=unused-argument
) -> None:
    finder = generate_pair_finder(top_directory, None)
    assert mock_algorithm.call_count > 0
    check_correct_results(finder, image_files)


def test_filled_hash_store_does_not_calculate_hash_values(
        top_directory: TemporaryDirectory, image_files: List[Path],
        reset_call_count  # pylint: disable=unused-argument
) -> None:
    hash_store = {path: MOCK_IMAGE_HASH_VALUE for path in image_files}
    generate_pair_finder(top_directory, hash_store)
    assert mock_algorithm.call_count == 0


def test_empty_hash_store_is_filled(
        top_directory: TemporaryDirectory, reset_call_count  # pylint: disable=unused-argument
) -> None:
    finder = generate_pair_finder(top_directory, None)
    original_call_number = mock_algorithm.call_count
    finder.get_pairs()
    assert mock_algorithm.call_count == original_call_number


@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_hash_store_is_written(
        top_directory: TemporaryDirectory, hash_store_path: Path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    assert hash_store_path.is_file()


@pytest.mark.parametrize('file_type', ['pickle'])
def test_pickle_file_contains_correct_hashes(
        top_directory: TemporaryDirectory, image_files: List[Path], hash_store_path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    with hash_store_path.open('rb') as pickle_file:
        written_hashes = pickle.load(pickle_file)
    for file_name in image_files:
        assert file_name in written_hashes
        assert written_hashes[file_name] == MOCK_IMAGE_HASH_VALUE


@pytest.mark.parametrize('file_type', ['json'])
def test_json_file_contains_correct_hashes(
        top_directory: TemporaryDirectory, image_files: List[Path], hash_store_path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    with hash_store_path.open('r') as json_file:
        written_hashes = json.load(json_file)
    for file_name in image_files:
        assert str(file_name) in written_hashes
        assert written_hashes[str(file_name)] == str(MOCK_IMAGE_HASH_VALUE)


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


def image_list(top_directory: TemporaryDirectory) -> List[Path]:
    return sorted(duplicate.files_in_dirs([top_directory.name]))


def generate_pair_finder(
        top_directory: TemporaryDirectory, hash_store: Optional[Cache]
) -> ImagePairFinder:
    return ImagePairFinder.create(
        image_list(top_directory), mock_algorithm, PairFinderOptions(slow=True),
        hash_store=hash_store
    )


def create_verified_hash_store(top_directory: TemporaryDirectory, store_path: Path) -> None:
    with PickleHashStore.create(store_path) as hash_store:
        finder = generate_pair_finder(top_directory, hash_store)
        finder.get_pairs()


def check_correct_results(finder: ImagePairFinder, images: List[Path]) -> None:
    pairs = finder.get_pairs()
    expected_pairs = combinations(images, 2)
    expected_pairs_string = f'{[(p[0].name, p[1].name) for p in pairs]}'
    for pair in expected_pairs:
        assert pair in pairs or (pair[1], pair[0]) in pairs, \
            f'{pair[0].name}, {pair[1].name} not in {expected_pairs_string}'
