__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from subprocess import call  # noqa: S404
from typing import Dict, Tuple, List

import imagehash

from duplicate_images.common import path_with_parent
from duplicate_images.function_types import ActionFunction

__all__ = ['call', 'quote', 'IMAGE_HASH_ALGORITHM', 'ACTIONS_ON_EQUALITY']


@lru_cache(maxsize=None)
def get_size(file: Path) -> int:
    return file.stat().st_size


@lru_cache(maxsize=None)
def get_hash(file: Path) -> str:
    return sha256(file.open('rb').read()).hexdigest()


def compare_exactly(file: Path, other_file: Path) -> bool:
    """Returns True if file and other_file are exactly exactly_equal"""
    return get_size(other_file) == get_size(file) and get_hash(file) == get_hash(other_file)


def ascending_by_size(pair: Tuple[Path, Path]) -> List[Path]:
    return sorted(pair, key=lambda path: path.stat().st_size)


def delete_with_log_message(file: Path) -> None:
    file.unlink()
    logging.info("Deleted %s", path_with_parent(file))


def quote(string: str) -> str:
    if '"' in string:
        if "'" in string:
            raise ValueError(f"{string} contains both single and double quotes, giving up")
        quotes = "'"
    else:
        quotes = '"'
    return f"{quotes}{string}{quotes}"


def quote_print(pair: Tuple[Path, Path]) -> None:
    print(f"{quote(str(pair[0]))} {quote(str(pair[1]))}")


IMAGE_HASH_ALGORITHM = {
    'ahash': imagehash.average_hash,
    'colorhash': imagehash.colorhash,
    'dhash': imagehash.dhash,
    'phash': imagehash.phash,
    'whash': imagehash.whash
}

ACTIONS_ON_EQUALITY: Dict[str, ActionFunction] = {
    'delete-first': lambda pair: delete_with_log_message(pair[0]),
    'd1': lambda pair: delete_with_log_message(pair[0]),
    'delete-second': lambda pair: delete_with_log_message(pair[1]),
    'd2': lambda pair: delete_with_log_message(pair[1]),
    'delete-bigger': lambda pair: delete_with_log_message(ascending_by_size(pair)[-1]),
    'd>': lambda pair: delete_with_log_message(ascending_by_size(pair)[-1]),
    'delete-smaller': lambda pair: delete_with_log_message(ascending_by_size(pair)[0]),
    'd<': lambda pair: delete_with_log_message(ascending_by_size(pair)[0]),
    'eog': lambda pair: call(["eog"] + [str(pic) for pic in pair]),  # noqa: S603
    'xv': lambda pair: call(["xv", "-nolim"] + [str(pic) for pic in pair]),  # noqa: S603
    'print': lambda pair: print(pair[0], pair[1]),
    'quote': quote_print,
    'none': lambda pair: None
}
