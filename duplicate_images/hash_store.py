"""
Persistent storage for calculated image hashes
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import json
import logging
import pickle  # nosec
from threading import Lock
from pathlib import Path
from typing import Any, IO, Callable, List, Optional, Union, Dict, Tuple

from imagehash import hex_to_hash

from duplicate_images.common import log_execution_time
from duplicate_images.function_types import Cache, CacheKey, Hash, is_hash


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

    def get(self, _: Path) -> Optional[Hash]:
        return None

    def add(self, _: Path, __: Hash) -> None:
        pass


HashStore = Union[NullHashStore, 'FileHashStore', 'PickleHashStore', 'JSONHashStore']


def is_valid_key(key: Any) -> bool:
    """Is `key` a tuple of (Path, mtime, size)?"""
    return (isinstance(key, tuple) and len(key) == 3
            and isinstance(key[0], Path)
            and isinstance(key[1], (int, float))
            and isinstance(key[2], int))


def migrate_keys(values: Dict[Union[Path, CacheKey], Hash]) -> Cache:
    """
    Old format: keys are plain Paths, with no file metadata. They are migrated to composite keys
    with dummy metadata (0.0, 0), which never matches a real file, so these files are rehashed on
    first access. Raises `ValueError` if any key is not a `Path` or a valid composite key.
    """
    migrated_values: Cache = {}
    migrated = False
    for key, hash_val in values.items():
        if isinstance(key, Path):
            migrated_values[(key, 0.0, 0)] = hash_val
            migrated = True
        elif is_valid_key(key):
            migrated_values[key] = hash_val
        else:
            raise ValueError(f'Invalid cache key format: {key}')
    if migrated:
        logging.info('Migrated old hash database format to new format with file metadata')
    return migrated_values


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
        self._lock = Lock()
        self._set_values({})
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

    def __exit__(self, exc_type: Any, _: Any, __: Any) -> None:
        # Don't save cache if interrupted by user - prevents corrupted partial cache
        if exc_type is KeyboardInterrupt:
            logging.info('Scan interrupted - cache not updated')
            return

        if not self.dirty:
            return
        if self.store_path.is_file():
            if self.store_path.with_suffix('.bak').is_file():
                self.store_path.with_suffix('.bak').unlink()
            self.store_path.rename(self.store_path.with_suffix('.bak'))
        self.dump()

    def _set_values(self, values: Cache) -> None:
        """Replace all cached values and rebuild the path index (path -> cache key)"""
        self.values: Cache = {}
        self._index: Dict[Path, CacheKey] = {}
        for key, image_hash in values.items():
            self._insert(key, image_hash)

    def _insert(self, key: CacheKey, image_hash: Hash) -> None:
        """Insert in place, dropping any older entry for the same path. Callers need the lock."""
        old_key = self._index.get(key[0])
        if old_key is not None and old_key != key:
            del self.values[old_key]
        self.values[key] = image_hash
        self._index[key[0]] = key

    def add(self, file: Path, image_hash: Hash) -> None:
        stat = file.stat()
        # may be called from several threads (ParallelImageHashScanner): mutate in place
        # under a lock, and use the index to drop a stale entry for this path in O(1)
        with self._lock:
            self._insert((file.resolve(), stat.st_mtime, stat.st_size), image_hash)
            self.dirty = True

    def get(self, file: Path) -> Optional[Hash]:
        stat = file.stat()
        key = (file.resolve(), stat.st_mtime, stat.st_size)
        return self.values.get(key)

    def metadata(self) -> Dict:
        return {'algorithm': self.algorithm, **self.hash_size_kwargs}

    def values_with_metadata(self) -> Tuple[Dict, Dict]:
        return self.values, self.metadata()

    def checked_load(
            self, file: IO,
            load: Callable[[IO], Tuple[Dict[Union[Path, CacheKey], Hash], Dict]]
    ) -> None:
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

        migrated_values = migrate_keys(values)

        bad_values = [value for value in migrated_values.values() if not is_hash(value)]
        if bad_values:
            raise ValueError(f'Not an image hash: {bad_values}')
        if metadata['algorithm'] != self.algorithm:
            raise ValueError(f'Algorithm mismatch: {metadata['algorithm']} != {self.algorithm}')
        if metadata != self.metadata():
            raise ValueError(f'Metadata mismatch: {metadata} != {self.metadata()}')
        self._set_values(migrated_values)

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


def load_values_and_metadata(file: IO) -> Tuple[Dict[Union[Path, CacheKey], Hash], Dict]:
    """
    Two JSON formats are understood, both as `[values, metadata]`:
    - old: `values` is a dict `{path: hash}`
    - current: `values` is a list of `[path, mtime, size, hash]`
    """
    try:
        valds = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError('Save file not in JSON format') from error
    if not isinstance(valds, list) or len(valds) != 2:
        raise ValueError('Save file not in format: [values, metadata]')
    values, metadata = valds
    if not isinstance(metadata, dict):
        raise ValueError(f'Metadata not a dict: {metadata}')

    parsed_values: Dict[Union[Path, CacheKey], Hash] = {}
    if isinstance(values, dict):
        for path, hash_string in values.items():
            parsed_values[Path(path).resolve()] = hex_to_hash(str(hash_string))
    elif isinstance(values, list):
        for entry in values:
            try:
                path, mtime, size, hash_string = entry
                key = (Path(path), float(mtime), int(size))
            except (TypeError, ValueError) as error:
                raise ValueError(f'Invalid cache entry: {entry}') from error
            parsed_values[key] = hex_to_hash(str(hash_string))
    else:
        raise ValueError(f'Not a dict or list: {values}')

    return parsed_values, metadata


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
    def converted_values(self) -> List[List[Any]]:
        # a list of [path, mtime, size, hash] avoids having to encode the key in a string
        with self._lock:
            return [
                [str(path), mtime, size, str(image_hash)]
                for (path, mtime, size), image_hash in self.values.items()
            ]

    @log_execution_time()
    def dump(self) -> None:
        with self.store_path.open('w') as file:
            json.dump((self.converted_values(), self.metadata()), file)
