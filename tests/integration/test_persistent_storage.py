
import json
import pickle
from pathlib import Path
from typing import Any, Tuple, Optional
from unittest.mock import Mock, patch

import pytest

from duplicate_images.duplicate import get_matches
from duplicate_images.pair_finder_options import PairFinderOptions


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle', 'json'])
@patch('imagehash.average_hash', return_value=0)
def test_open_hash_store_with_filename(
        average_hash: Mock, data_dir: Path, test_set: str, file_type: str
) -> None:
    folder = data_dir / test_set
    cache_file = folder.with_suffix(f'.{file_type}')
    creation_time = cache_file.stat().st_ctime
    get_matches([folder], 'phash', hash_store_path=cache_file)
    assert average_hash.call_count == 0
    assert cache_file.stat().st_ctime > creation_time


@pytest.mark.parametrize('test_set', ['different', 'equal_but_binary_different'])
def test_open_bad_file_format(data_dir: Path, test_set: str) -> None:
    folder = data_dir / test_set
    cache_file = data_dir / 'garbage.txt'
    creation_time = cache_file.stat().st_ctime
    with pytest.raises(ValueError):
        get_matches([folder], 'phash', hash_store_path=cache_file)
    assert cache_file.stat().st_ctime == creation_time


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_open_correct_file_format_but_not_a_tuple(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str
) -> None:
    check_garbage(
        tmp_dir, data_dir / test_set, file_type, garbage_data='garbage', message=None
    )


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_open_correct_file_format_but_values_not_a_dict(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str
) -> None:
    check_garbage(
        tmp_dir, data_dir / test_set, file_type, garbage_data=('garbage', {}), message='Not a dict'
    )


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_open_correct_file_format_but_metadata_not_a_dict(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str
) -> None:
    check_garbage(
        tmp_dir, data_dir / test_set, file_type, garbage_data=({}, 'garbage'),
        message='Metadata not a dict'
    )


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle'])
def test_open_correct_file_format_but_keys_not_paths(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str
) -> None:
    folder = data_dir / test_set
    check_garbage(
        tmp_dir, folder, file_type,
        garbage_data=(
            {str(path): 0 for path in folder.glob('**')}, {'algorithm': 'phash', 'hash_size': 8}
        ),
        message='Not a Path'
    )


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle'])
def test_open_correct_file_format_but_values_not_image_hashes(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str
) -> None:
    folder = data_dir / test_set
    check_garbage(
        tmp_dir, folder, file_type,
        garbage_data=(
            {path: 0 for path in folder.glob('**')}, {'algorithm': 'phash', 'hash_size': 8}
        ), message='Not an image hash'
    )


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_open_correct_file_format_but_metadata_missing(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str
) -> None:
    folder = data_dir / test_set
    check_garbage(
        tmp_dir, folder, file_type,
        garbage_data=({path: 0 for path in folder.glob('**')}, ), message=None
    )


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle', 'json'])
def test_open_correct_file_format_but_metadata_empty(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str
) -> None:
    folder = data_dir / test_set
    check_garbage(
        tmp_dir, folder, file_type,
        garbage_data=({path: 0 for path in folder.glob('**')}, {}), message='Metadata empty'
    )


@pytest.mark.parametrize('test_set', ['different', 'equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle', 'json'])
@pytest.mark.parametrize('algorithms', [('phash', 'ahash')])
def test_opening_with_different_algorithm_leads_to_error(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str, algorithms: Tuple[str, str]
) -> None:
    cache_file = tmp_dir / f'hash_store.{file_type}'
    get_matches([data_dir / test_set], algorithms[0], hash_store_path=cache_file)
    with pytest.raises(ValueError, match='Algorithm mismatch'):
        get_matches([data_dir / test_set], algorithms[1], hash_store_path=cache_file)


@pytest.mark.parametrize('test_set', ['different', 'equal_but_binary_different'])
@pytest.mark.parametrize('file_type', ['pickle', 'json'])
@pytest.mark.parametrize('hash_size', [(8, 9)])
def test_opening_with_different_algorithm_parameters_leads_to_error(
        tmp_dir: Path, data_dir: Path, test_set: str, file_type: str, hash_size: Tuple[int, int]
) -> None:
    cache_file = tmp_dir / f'hash_store.{file_type}'
    get_matches(
        [data_dir / test_set], 'phash', options=PairFinderOptions(hash_size=hash_size[0]),
        hash_store_path=cache_file
    )
    with pytest.raises(ValueError, match='Metadata mismatch'):
        get_matches(
            [data_dir / test_set], 'phash', options=PairFinderOptions(hash_size=hash_size[1]),
            hash_store_path=cache_file
        )


def check_garbage(
        temp_dir: Path, folder: Path, file_type: str, garbage_data: Any, message: Optional[str]
) -> None:
    cache_file = temp_dir / f'garbage.{file_type}'
    if file_type == 'pickle':
        dump_pickle(cache_file, garbage_data)
    else:
        dump_json(cache_file, garbage_data)
    creation_time = cache_file.stat().st_ctime
    with pytest.raises(ValueError, match=message):
        get_matches([folder], 'phash', hash_store_path=cache_file)
    assert cache_file.stat().st_ctime == creation_time


def dump_pickle(cache_file: Path, garbage_data: Any):
    with cache_file.open('wb') as file:
        pickle.dump(garbage_data, file)


def dump_json(cache_file: Path, garbage_data: Any):
    with cache_file.open('w') as file:
        json.dump(encode_dict_keys_to_str(garbage_data), file)


def encode_dict_keys_to_str(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(key): value for key, value in obj.items()}
    if isinstance(obj, tuple):
        return tuple(encode_dict_keys_to_str(item) for item in obj)
    return obj
