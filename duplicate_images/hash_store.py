__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
import pickle  # noqa: S403
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

from imagehash import ImageHash

from duplicate_images.function_types import Cache


class NullHashStore:

    def __init__(self) -> None:
        logging.info('No persistent storage for calculated image hashes set up')

    def __enter__(self) -> Cache:
        return {}

    def __exit__(self, _: Any, __: Any, ___: Any) -> None:
        pass


class PickleHashStore:

    @classmethod
    def create(cls, store_path: Optional[Path]) -> Union['PickleHashStore', NullHashStore]:
        return PickleHashStore(store_path) if store_path is not None else NullHashStore()

    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self.values: Cache = {}
        try:
            with store_path.open('rb') as file:
                self.values = checked_load(file)
            logging.info(
                'Opened persistent storage %s with %d entries', store_path, len(self.values)
            )
        except (FileNotFoundError, EOFError, pickle.PickleError):
            logging.info('Creating new persistent storage at %s', store_path)

    def __enter__(self) -> Cache:
        return self.values

    def __exit__(self, _: Any, __: Any, ___: Any) -> None:
        if self.store_path.is_file():
            self.store_path.rename(self.store_path.with_suffix('.bak'))
        with self.store_path.open('wb') as file:
            pickle.dump(self.values, file)


def checked_load(file: BinaryIO) -> Cache:
    values = pickle.load(file)  # noqa: S301
    if not isinstance(values, dict):
        raise ValueError(f"Not a dict: {values}")
    bad_keys = [key for key in values.keys() if not isinstance(key, Path)]
    if bad_keys:
        raise ValueError(f"Not a Path: {bad_keys}")
    bad_values = [value for value in values.values() if not isinstance(value, ImageHash)]
    if bad_values:
        raise ValueError(f"Not an image hash: {bad_values}")
    return values


HashStore = Union[NullHashStore, PickleHashStore]
