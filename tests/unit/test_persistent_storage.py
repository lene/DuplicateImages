# pylint: disable=missing-docstring
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import json
import logging
import pickle
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from time import sleep
from typing import List

import pytest
from imagehash import hex_to_hash

from duplicate_images.duplicate import files_in_dirs, is_image_file
from duplicate_images.function_types import Cache, CacheKey
from duplicate_images.image_pair_finder import ImagePairFinder
from duplicate_images.pair_finder_options import PairFinderOptions
from duplicate_images.hash_store import (
    PickleHashStore, JSONHashStore, FileHashStore, HashStore, NullHashStore
)
from .conftest import (
    MOCK_IMAGE_HASH_VALUE, mock_algorithm, create_jpg_and_png, create_image, IMAGE_WIDTH
)

DEFAULT_ALGORITHM = 'phash'
DEFAULT_HASH_SIZE = {'hash_size': 8}
DEFAULT_METADATA = {'algorithm': DEFAULT_ALGORITHM, **DEFAULT_HASH_SIZE}


class MockHashStore(FileHashStore):  # pylint: disable=abstract-method
    def __init__(self, values: Cache) -> None:  # pylint: disable=super-init-not-called
        self._lock = Lock()
        self._set_values(values)


def cache_key(path: Path) -> CacheKey:
    stat = path.stat()
    return path.resolve(), stat.st_mtime, stat.st_size


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
    hash_store = MockHashStore({cache_key(path): MOCK_IMAGE_HASH_VALUE for path in image_files})
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


@pytest.mark.parametrize('file_type', ['pickle'])
def test_pickle_file_contains_correct_hashes(
        top_directory: TemporaryDirectory, image_files: List[Path], hash_store_path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    with hash_store_path.open('rb') as pickle_file:
        written_hashes = pickle.load(pickle_file)[0]
    hashes_by_path = {key[0]: value for key, value in written_hashes.items()}
    for file_name in image_files:
        assert hashes_by_path[file_name.resolve()] == MOCK_IMAGE_HASH_VALUE
        assert cache_key(file_name) in written_hashes


@pytest.mark.parametrize('file_type', ['json'])
def test_json_file_contains_correct_hashes(
        top_directory: TemporaryDirectory, image_files: List[Path], hash_store_path
) -> None:
    create_verified_hash_store(top_directory, hash_store_path)
    with hash_store_path.open('r') as json_file:
        written_hashes = json.load(json_file)[0]
    hashes_by_path = {entry[0]: entry[3] for entry in written_hashes}
    for file_name in image_files:
        assert hashes_by_path[str(file_name.resolve())] == str(MOCK_IMAGE_HASH_VALUE)
        assert [str(file_name.resolve()), *cache_key(file_name)[1:]] in [
            entry[:3] for entry in written_hashes
        ]


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
        assert str(written_hashes[cache_key(file_name)]) == str(MOCK_IMAGE_HASH_VALUE)


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
    assert hash_store.values == {
        cache_key(path): MOCK_IMAGE_HASH_VALUE for path in image_list(top_directory)
    }


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


@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_file_replacement_recalculates_hash(
        top_directory: TemporaryDirectory, hash_store_path: Path,
        reset_call_count  # pylint: disable=unused-argument
) -> None:
    """Test that replacing a file at the same path forces hash recalculation (issue #19)"""
    # Create initial file and populate cache
    file_path = Path(top_directory.name) / 'test_image.jpg'
    create_image(file_path, IMAGE_WIDTH)
    initial_mtime = file_path.stat().st_mtime

    with FileHashStore.create(hash_store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as hash_store:
        finder = ImagePairFinder.create(
            [file_path], mock_algorithm, options=PairFinderOptions(slow=True),
            hash_store=hash_store
        )
        finder.get_equal_groups()

    initial_call_count = mock_algorithm.call_count
    assert initial_call_count > 0, 'Hash should be calculated for new file'

    # Sleep to ensure different mtime
    sleep(0.01)

    # Replace file with different content (different size)
    file_path.unlink()
    create_image(file_path, IMAGE_WIDTH * 2)  # Different size
    new_mtime = file_path.stat().st_mtime
    assert new_mtime != initial_mtime, 'File replacement should change mtime'

    # Scan again with same cache - should recalculate because file changed
    mock_algorithm.call_count = 0
    with FileHashStore.create(hash_store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as hash_store:
        finder = ImagePairFinder.create(
            [file_path], mock_algorithm, options=PairFinderOptions(slow=True),
            hash_store=hash_store
        )
        finder.get_equal_groups()

    assert mock_algorithm.call_count > 0, \
        'Hash should be recalculated when file is replaced (issue #19 fix)'


OLD_FORMAT_PATHS = ['image.jpg', 'with|pipe.jpg', 'with|1.5|7.jpg']


def old_format_store_files(tmp_path: Path) -> List[Path]:
    files = [tmp_path / name for name in OLD_FORMAT_PATHS]
    for file in files:
        file.write_text(file.name)
    return files


def check_old_cache_migrated(store: FileHashStore, files: List[Path]) -> None:
    assert len(store.values) == len(files)
    for file in files:
        # old entries have no mtime/size, so they never match: the file is rehashed
        assert store.get(file) is None
        assert (file.resolve(), 0.0, 0) in store.values
    store.add(files[0], MOCK_IMAGE_HASH_VALUE)
    assert store.get(files[0]) == MOCK_IMAGE_HASH_VALUE
    assert (files[0].resolve(), 0.0, 0) not in store.values  # stale migrated entry dropped
    assert len(store.values) == len(files)


def test_old_format_pickle_cache_with_path_keys_is_migrated(tmp_path: Path) -> None:
    files = old_format_store_files(tmp_path)
    store_path = tmp_path / 'old.pickle'
    with store_path.open('wb') as file:
        pickle.dump(
            ({path.resolve(): MOCK_IMAGE_HASH_VALUE for path in files}, DEFAULT_METADATA), file
        )
    check_old_cache_migrated(
        PickleHashStore(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE), files
    )


def test_old_format_json_cache_without_composite_keys_is_migrated(tmp_path: Path) -> None:
    """Old JSON format: a dict of path -> hash, including paths that contain `|`"""
    files = old_format_store_files(tmp_path)
    store_path = tmp_path / 'old.json'
    with store_path.open('w') as file:
        json.dump(
            ({str(path.resolve()): str(MOCK_IMAGE_HASH_VALUE) for path in files}, DEFAULT_METADATA),
            file
        )
    check_old_cache_migrated(JSONHashStore(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE), files)


@pytest.mark.parametrize(
    'store_class,suffix', [(PickleHashStore, 'pickle'), (JSONHashStore, 'json')]
)
def test_new_format_roundtrip_with_special_characters_in_path(
        tmp_path: Path, store_class, suffix: str
) -> None:
    file = tmp_path / 'a|1.0|2.jpg'
    file.write_text('x')
    store_path = tmp_path / f'store.{suffix}'
    with store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE) as store:
        store.add(file, MOCK_IMAGE_HASH_VALUE)
    loaded = store_class(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
    assert str(loaded.get(file)) == str(MOCK_IMAGE_HASH_VALUE)


def test_json_cache_with_malformed_entry_raises_value_error(tmp_path: Path) -> None:
    store_path = tmp_path / 'bad.json'
    with store_path.open('w') as file:
        entry = ['path', 'not a number', 1, str(MOCK_IMAGE_HASH_VALUE)]
        json.dump(([entry], DEFAULT_METADATA), file)
    with pytest.raises(ValueError, match='Invalid cache entry'):
        JSONHashStore(store_path, DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)


def test_add_replaces_stale_entry_for_same_path_in_place(tmp_path: Path) -> None:
    file = tmp_path / 'image.jpg'
    file.write_text('a')
    store = JSONHashStore(tmp_path / 'store.json', DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
    values_before = store.values
    store.add(file, MOCK_IMAGE_HASH_VALUE)
    file.write_text('longer content')
    other_hash = hex_to_hash('0' * 16)
    store.add(file, other_hash)
    assert store.values is values_before, 'values must be mutated in place, not rebound'
    assert list(store.values.values()) == [other_hash]
    assert store.get(file) == other_hash


def test_concurrent_adds_lose_no_entries(tmp_path: Path) -> None:
    files = [tmp_path / f'image{i}.jpg' for i in range(500)]
    for file in files:
        file.write_text(file.name)
    store = JSONHashStore(tmp_path / 'store.json', DEFAULT_ALGORITHM, DEFAULT_HASH_SIZE)
    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(lambda file: store.add(file, MOCK_IMAGE_HASH_VALUE), files))
    assert len(store.values) == len(files)
    assert all(store.get(file) is not None for file in files)
