
import json
import pickle
from pathlib import Path
from typing import Any, Tuple
from unittest.mock import Mock, patch

import pytest

from duplicate_images.duplicate import get_matches


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle', 'json'])
@patch('imagehash.average_hash', return_value=0)
def test_open_hash_store_with_filename(
        average_hash: Mock, data_dir: Path, test_set: str, file_type: str
) -> None:
    folder = data_dir / test_set
    cache_file = folder.with_suffix(f'.{file_type}')
    creation_time = cache_file.stat().st_ctime
    get_matches([folder], 'ahash', hash_store_path=cache_file)
    assert average_hash.call_count == 0
    assert cache_file.stat().st_ctime > creation_time


@pytest.mark.parametrize('test_set', ['different', 'equal_but_binary_different'])
def test_open_bad_file_format(data_dir: Path, test_set: str) -> None:
    folder = data_dir / test_set
    cache_file = data_dir / 'garbage.txt'
    creation_time = cache_file.stat().st_ctime
    with pytest.raises(ValueError):
        get_matches([folder], 'ahash', hash_store_path=cache_file)
    assert cache_file.stat().st_ctime == creation_time


@pytest.mark.parametrize('test_set', ['different', 'equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle'])
def test_open_correct_file_format_but_bad_data_format(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str
) -> None:
    check_garbage(
        tmp_dir, data_dir / test_set, file_type, garbage_data='garbage', message='Not a dict'
    )


@pytest.mark.parametrize('test_set', ['different', 'equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle'])
def test_open_correct_file_format_but_keys_not_paths(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str
) -> None:
    folder = data_dir / test_set
    check_garbage(
        tmp_dir, folder, file_type,
        garbage_data={str(path): 0 for path in folder.glob('**')}, message='Not a Path'
    )


@pytest.mark.parametrize('test_set', ['different', 'equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle'])
def test_open_correct_file_format_but_values_not_image_hashes(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str
) -> None:
    folder = data_dir / test_set
    check_garbage(
        tmp_dir, folder, file_type,
        garbage_data={path: 0 for path in folder.glob('**')}, message='Not an image hash'
    )


@pytest.mark.parametrize('test_set', ['different', 'equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle'])
@pytest.mark.parametrize('algorithms', [('phash', 'ahash')])
def test_opening_with_different_algorithm_leads_to_error(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str, algorithms: Tuple[str, str]
) -> None:
    cache_file = tmp_dir / f'hash_store.{file_type}'
    get_matches([data_dir / test_set], algorithms[0], hash_store_path=cache_file)
    with pytest.raises(ValueError):
        get_matches([data_dir / test_set], algorithms[1], hash_store_path=cache_file)


def check_garbage(
        temp_dir: Path, folder: Path, file_type: str, garbage_data: Any, message: str
) -> None:
    cache_file = temp_dir / f'garbage.{file_type}'
    if file_type == 'pickle':
        dump_pickle(cache_file, garbage_data)
    else:
        dump_json(cache_file, garbage_data)
    creation_time = cache_file.stat().st_ctime
    with pytest.raises(ValueError, match=message):
        get_matches([folder], 'ahash', hash_store_path=cache_file)
    assert cache_file.stat().st_ctime == creation_time


def dump_pickle(cache_file: Path, garbage_data: Any):
    with cache_file.open('wb') as file:
        pickle.dump(garbage_data, file)


def dump_json(cache_file: Path, garbage_data: Any):
    with cache_file.open('w') as file:
        json.dump(garbage_data, file)
