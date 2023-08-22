__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import json
import logging
import pickle  # nosec
from pathlib import Path
from typing import Any, IO, Callable, Optional, Union

from imagehash import ImageHash, hex_to_hash

from duplicate_images.common import log_execution_time
from duplicate_images.function_types import Cache


class NullHashStore:

    def __init__(self) -> None:
        logging.info('No persistent storage for calculated image hashes set up')

    def __enter__(self) -> Cache:
        return {}

    def __exit__(self, _: Any, __: Any, ___: Any) -> None:
        pass


class FileHashStore:

    @classmethod
    def create(cls, store_path: Optional[Path]) -> Union['FileHashStore', NullHashStore]:
        if store_path is None:
            return NullHashStore()
        if store_path.suffix == '.pickle':
            return PickleHashStore(store_path)
        return JSONHashStore(store_path)

    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self.values: Cache = {}
        try:
            self.load()
            logging.info(
                'Opened persistent storage %s with %d entries', store_path, len(self.values)
            )
        except (FileNotFoundError, EOFError, pickle.PickleError):
            logging.info('Creating new persistent storage at %s', store_path)

    def __enter__(self) -> Cache:
        return self.values

    def __exit__(self, _: Any, __: Any, ___: Any) -> None:
        if self.store_path.is_file():
            if self.store_path.with_suffix('.bak').is_file():
                self.store_path.with_suffix('.bak').unlink()
            self.store_path.rename(self.store_path.with_suffix('.bak'))
        self.dump()

    def load(self) -> None:
        raise NotImplementedError()

    def dump(self) -> None:
        raise NotImplementedError()


class PickleHashStore(FileHashStore):

    @log_execution_time()
    def load(self) -> None:
        with self.store_path.open('rb') as file:
            self.values = checked_load(file, pickle.load)

    @log_execution_time()
    def dump(self) -> None:
        with self.store_path.open('wb') as file:
            pickle.dump(self.values, file)  # nosec


class JSONHashStore(FileHashStore):

    @log_execution_time()
    def load(self) -> None:
        with self.store_path.open('r') as file:
            self.values = checked_load(
                file,
                lambda f: {Path(k): hex_to_hash(v) for k, v in json.load(f).items()}
            )

    @log_execution_time()
    def dump(self) -> None:
        with self.store_path.open('w') as file:
            json.dump({str(k.resolve()): str(v) for k, v in self.values.items()}, file)


def checked_load(file: IO, load: Callable[[IO], Cache]) -> Cache:
    values = load(file)  # nosec
    if not isinstance(values, dict):
        raise ValueError(f'Not a dict: {values}')
    bad_keys = [key for key in values.keys() if not isinstance(key, Path)]
    if bad_keys:
        raise ValueError(f'Not a Path: {bad_keys}')
    bad_values = [value for value in values.values() if not isinstance(value, ImageHash)]
    if bad_values:
        raise ValueError(f'Not an image hash: {bad_values}')
    return values


HashStore = Union[NullHashStore, PickleHashStore, JSONHashStore]
