
import pickle
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from duplicate_images.duplicate import get_matches


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
@patch('imagehash.average_hash', return_value=0)
def test_open_hash_store_with_filename(average_hash: Mock, data_dir: Path, test_set: str) -> None:
    folder = data_dir / test_set
    cache_file = folder.with_suffix('.pickle')
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
def test_open_correct_file_format_but_bad_data_format(
        tmp_dir: Path, data_dir: Path, test_set: str
) -> None:
    check_garbage(tmp_dir, data_dir / test_set, garbage_data='garbage', message="Not a dict")


@pytest.mark.parametrize('test_set', ['different', 'equal_but_binary_different'])
def test_open_correct_file_format_but_keys_not_paths(
        tmp_dir: Path, data_dir: Path, test_set: str
) -> None:
    folder = data_dir / test_set
    check_garbage(
        tmp_dir, folder,
        garbage_data={str(path): 0 for path in folder.glob("**")}, message="Not a Path"
    )


@pytest.mark.parametrize('test_set', ['different', 'equal_but_binary_different'])
def test_open_correct_file_format_but_values_not_image_hashes(
        tmp_dir: Path, data_dir: Path, test_set: str
) -> None:
    folder = data_dir / test_set
    check_garbage(
        tmp_dir, folder,
        garbage_data={path: 0 for path in folder.glob("**")}, message="Not an image hash"
    )


def check_garbage(temp_dir: Path, folder: Path, garbage_data: Any, message: str) -> None:
    cache_file = temp_dir / 'garbage.pickle'
    with cache_file.open('wb') as pickle_file:
        pickle.dump(garbage_data, pickle_file)
    creation_time = cache_file.stat().st_ctime
    with pytest.raises(ValueError, match=message):
        get_matches([folder], 'ahash', hash_store_path=cache_file)
    assert cache_file.stat().st_ctime == creation_time
