"""
Persistent storage for calculated image hashes
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import json
import logging
import pickle  # nosec
from pathlib import Path
from typing import Any, IO, Callable, Optional, Union, Dict, Tuple

from imagehash import ImageHash, hex_to_hash

from duplicate_images.common import log_execution_time
from duplicate_images.function_types import Cache


class NullHashStore:
    """
    Hash store that does not store anything but can be used as a drop-in
    replacement for `FileHashStore` and `PickleHashStore` when no persistent
    storage is desired
    """

    def __init__(self) -> None:
        logging.info('No persistent storage for calculated image hashes set up')

    def __enter__(self) -> 'NullHashStore':
        return self

    def __exit__(self, _: Any, __: Any, ___: Any) -> None:
        pass

    def get(self, _: Path) -> Optional[ImageHash]:
        return None

    def add(self, _: Path, __: ImageHash) -> None:
        pass


HashStore = Union[NullHashStore, 'FileHashStore', 'PickleHashStore', 'JSONHashStore']


class FileHashStore:
    """
    Base class for persistent storage of calculated image hashes, providing all
    necessary functionality except for reading and writing data to various file
    formats
    """
    @staticmethod
    def create(
            store_path: Optional[Path], algorithm: str, hash_size_kwargs: Dict
    ) -> Union['FileHashStore', NullHashStore]:
        if store_path is None:
            return NullHashStore()
        if store_path.suffix == '.pickle':
            return PickleHashStore(store_path, algorithm, hash_size_kwargs)
        return JSONHashStore(store_path, algorithm, hash_size_kwargs)

    def __init__(self, store_path: Path, algorithm: str, hash_size_kwargs: Dict) -> None:
        self.store_path = store_path
        self.algorithm = algorithm
        self.hash_size_kwargs = hash_size_kwargs
        self.values: Cache = {}
        self.dirty: bool = False
        try:
            self.load()
            logging.info(
                'Opened persistent storage %s with %d entries', store_path, len(self.values)
            )
        except (FileNotFoundError, EOFError, pickle.PickleError):
            logging.info('Creating new %s at %s', self.__class__.__name__, store_path)

    def __enter__(self) -> 'FileHashStore':
        return self

    def __exit__(self, _: Any, __: Any, ___: Any) -> None:
        if not self.dirty:
            return
        if self.store_path.is_file():
            if self.store_path.with_suffix('.bak').is_file():
                self.store_path.with_suffix('.bak').unlink()
            self.store_path.rename(self.store_path.with_suffix('.bak'))
        self.dump()

    def add(self, file: Path, image_hash: ImageHash) -> None:
        self.values[file] = image_hash
        self.dirty = True

    def get(self, file: Path) -> Optional[ImageHash]:
        return self.values.get(file)

    def metadata(self) -> Dict:
        return {'algorithm': self.algorithm, **self.hash_size_kwargs}

    def values_with_metadata(self) -> Tuple[Dict, Dict]:
        return self.values, self.metadata()

    def checked_load(self, file: IO, load: Callable[[IO], Tuple[Cache, Dict]]) -> None:
        try:
            values, metadata = load(file)  # nosec
        except IndexError as error:
            raise ValueError('Save file not in format: [values, metadata]') from error
        if not isinstance(values, dict):
            raise ValueError(f'Not a dict: {values}')
        if not metadata:
            raise ValueError('Metadata empty')
        if not isinstance(metadata, dict):
            raise ValueError(f'Metadata not a dict: {metadata}')
        bad_keys = [key for key in values.keys() if not isinstance(key, Path)]
        if bad_keys:
            raise ValueError(f'Not a Path: {bad_keys}')
        bad_values = [value for value in values.values() if not isinstance(value, ImageHash)]
        if bad_values:
            raise ValueError(f'Not an image hash: {bad_values}')
        if metadata['algorithm'] != self.algorithm:
            raise ValueError(f'Algorithm mismatch: {metadata["algorithm"]} != {self.algorithm}')
        if metadata.keys() != self.metadata().keys():
            raise ValueError(f'Metadata mismatch: {metadata} != {self.metadata()}')
        if metadata != self.metadata():
            raise ValueError(f'Metadata mismatch: {metadata} != {self.metadata()}')
        self.values = values

    def load(self) -> None:
        raise NotImplementedError()

    def dump(self) -> None:
        raise NotImplementedError()


class PickleHashStore(FileHashStore):
    """
    Implementation of `FileHashStore` that reads and stores the calculated
    image hashes in Pickle format
    """

    @log_execution_time()
    def load(self) -> None:
        with self.store_path.open('rb') as file:
            self.checked_load(file, pickle.load)

    @log_execution_time()
    def dump(self) -> None:
        with self.store_path.open('wb') as file:
            pickle.dump(self.values_with_metadata(), file)  # nosec


def load_values_and_metadata(file: IO) -> Tuple[Cache, Dict]:
    try:
        valds = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError('Save file not in JSON format') from error
    if not isinstance(valds, list):
        raise ValueError('Save file not in format: [values, metadata]')
    if not isinstance(valds[0], dict):
        raise ValueError(f'Not a dict: {valds[0]}')
    if not isinstance(valds[1], dict):
        raise ValueError(f'Metadata not a dict: {valds[1]}')
    return {Path(k): hex_to_hash(str(v)) for k, v in valds[0].items()}, valds[1]


class JSONHashStore(FileHashStore):
    """
    Implementation of `FileHashStore` that reads and stores the calculated
    image hashes in JSON format
    """

    @log_execution_time()
    def load(self) -> None:
        with self.store_path.open('r') as file:
            self.checked_load(file, load_values_and_metadata)

    # see https://bugs.python.org/issue18820 for why this pain is necessary (Python does not allow
    # to automatically convert dict keys for JSON export
    def converted_values(self):
        return {str(k.resolve()): str(v) for k, v in self.values.items()}

    @log_execution_time()
    def dump(self) -> None:
        with self.store_path.open('w') as file:
            json.dump((self.converted_values(), self.metadata()), file)
