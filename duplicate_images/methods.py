"""
Definition of the possible actions run on sets of equal images
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from argparse import Namespace
from pathlib import Path
from shlex import quote
from subprocess import call  # nosec
from typing import Any, Callable, Dict, List, Optional

import imagehash

from duplicate_images.common import path_with_parent
from duplicate_images.function_types import ActionFunction, HashFunction, ImageGroup

__all__ = [
    'call', 'quote', 'get_hash_size_kwargs', 'IMAGE_HASH_ALGORITHM', 'ALGORITHM_DEFAULTS',
    'ACTIONS_ON_EQUALITY'
]


def ascending_by_size(group: ImageGroup) -> List[Path]:
    return sorted(group, key=lambda path: (path.stat().st_size, str(path)))


def delete_with_log_message(file: Path) -> None:
    file.unlink()
    logging.info('Deleted %s', path_with_parent(file))


def symlink_to_biggest_file(group: ImageGroup):
    biggest = ascending_by_size(group)[-1]
    others = set(group) - {biggest}
    for file in others:
        delete_with_log_message(file)
        file.symlink_to(biggest)


def shell_exec(args: Namespace, group: ImageGroup) -> None:
    cmd = args.exec
    for num, path in enumerate(group):
        cmd = cmd.replace(f"{'{'}{num + 1}{'}'}", f'{quote(str(path))}')
    cmd = cmd.replace('{*}', ' '.join([quote(str(path)) for path in group]))
    call(cmd, shell=True)  # nosec


def get_hash_size_kwargs(algorithm: HashFunction, size: Optional[int]) -> Dict[str, int]:
    if size is None:
        return ALGORITHM_DEFAULTS.get(algorithm, {'hash_size': 8})
    kwarg = next(iter(ALGORITHM_DEFAULTS.get(algorithm, {'hash_size': 8})))
    return {kwarg: size}


IMAGE_HASH_ALGORITHM = {
    'ahash': imagehash.average_hash,
    'phash': imagehash.phash,
    'phash_simple': imagehash.phash_simple,
    'dhash': imagehash.dhash,
    'dhash_vertical': imagehash.dhash_vertical,
    'whash': imagehash.whash,
    'colorhash': imagehash.colorhash,
}  # type: Dict[str, Callable[[Any], imagehash.ImageHash]]

ALGORITHM_DEFAULTS = {
    imagehash.average_hash: {'hash_size': 8},
    imagehash.phash: {'hash_size': 8},
    imagehash.phash_simple: {'hash_size': 8},
    imagehash.dhash: {'hash_size': 8},
    imagehash.dhash_vertical: {'hash_size': 8},
    imagehash.whash: {'hash_size': 8},
    imagehash.colorhash: {'binbits': 3},
}

ACTIONS_ON_EQUALITY: Dict[str, ActionFunction] = {
    'delete-first': lambda args, group: delete_with_log_message(group[0]),
    'd1': lambda args, group: delete_with_log_message(group[0]),
    'delete-last': lambda args, group: delete_with_log_message(group[-1]),
    'dl': lambda args, group: delete_with_log_message(group[-1]),
    'delete-biggest': lambda args, group: delete_with_log_message(ascending_by_size(group)[-1]),
    'd>': lambda args, group: delete_with_log_message(ascending_by_size(group)[-1]),
    'delete-smallest': lambda args, group: delete_with_log_message(ascending_by_size(group)[0]),
    'd<': lambda args, group: delete_with_log_message(ascending_by_size(group)[0]),
    'symlink-smaller': lambda args, group: symlink_to_biggest_file(group),
    'eog': lambda args, group: call(['eog'] + [str(pic) for pic in group]),  # nosec
    'xv': lambda args, group: call(['xv', '-nolim'] + [str(pic) for pic in group]),  # nosec
    'print': lambda args, group: print(*group),
    'print_inline': lambda args, group: print(*group, end=' '),
    'quote': lambda args, group: print(' '.join([quote(str(pic)) for pic in group])),
    'quote_inline': lambda args, group: print(
        ' '.join([quote(str(pic)) for pic in group]), end=' '
    ),
    'exec': lambda args, group: shell_exec(args, group),  # pylint: disable=unnecessary-lambda
    'none': lambda args, group: None,
}
