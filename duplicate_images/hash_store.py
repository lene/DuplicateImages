"""
Persistent storage for calculated image hashes
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import json
import logging
import pickle  # nosec
from pathlib import Path
from typing import Any, IO, Callable, Optional, Union, Dict, Tuple

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

    def add(self, file: Path, image_hash: Hash) -> None:
        stat = file.stat()
        resolved_path = file.resolve()

        # Remove any existing entries for this path to prevent cache bloat
        self.values = {k: v for k, v in self.values.items() if k[0] != resolved_path}

        # Add new entry with composite key (path, mtime, size)
        new_key = (resolved_path, stat.st_mtime, stat.st_size)
        self.values[new_key] = image_hash
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

        # Detect and migrate old format: Dict[Path, Hash] -> Dict[(Path, mtime, size), Hash]
        migrated_values: Cache = {}
        if values and not isinstance(next(iter(values.keys())), tuple):
            logging.info('Migrating old hash database format to new format with file metadata')
            # Old format: keys are Path objects, convert to composite keys with dummy metadata
            # Files with changed mtime/size will be recalculated on first access
            for path, hash_val in values.items():
                if isinstance(path, Path):
                    migrated_values[(path, 0.0, 0)] = hash_val
        else:
            # New format or already migrated - just cast to the right type
            for k, v in values.items():
                if isinstance(k, tuple):
                    migrated_values[k] = v

        # Validate keys are tuples of (Path, float, int)
        def is_valid_key(key):
            return (isinstance(key, tuple) and len(key) == 3
                    and isinstance(key[0], Path)
                    and isinstance(key[1], (int, float))
                    and isinstance(key[2], int))

        bad_keys = [key for key in migrated_values.keys() if not is_valid_key(key)]
        if bad_keys:
            raise ValueError(f'Invalid cache key format: {bad_keys}')

        bad_values = [value for value in migrated_values.values() if not is_hash(value)]
        if bad_values:
            raise ValueError(f'Not an image hash: {bad_values}')
        if metadata['algorithm'] != self.algorithm:
            raise ValueError(f'Algorithm mismatch: {metadata['algorithm']} != {self.algorithm}')
        if metadata.keys() != self.metadata().keys():
            raise ValueError(f'Metadata mismatch: {metadata} != {self.metadata()}')
        if metadata != self.metadata():
            raise ValueError(f'Metadata mismatch: {metadata} != {self.metadata()}')
        self.values = migrated_values

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

    # Parse keys: can be either "path" (old format) or "path|mtime|size" (new format)
    parsed_values: Dict[Union[Path, CacheKey], Hash] = {}
    for k, v in valds[0].items():
        if '|' in k:
            # New format: "path|mtime|size"
            parts = k.rsplit('|', 2)
            path = Path(parts[0]).resolve()
            mtime = float(parts[1])
            size = int(parts[2])
            parsed_values[(path, mtime, size)] = hex_to_hash(str(v))
        else:
            # Old format: just path (will be migrated in checked_load)
            parsed_values[Path(k).resolve()] = hex_to_hash(str(v))

    return parsed_values, valds[1]


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
        # Serialize composite keys as "path|mtime|size"
        return {
            f'{k[0].resolve()}|{k[1]}|{k[2]}': str(v)
            for k, v in self.values.items()
        }

    @log_execution_time()
    def dump(self) -> None:
        with self.store_path.open('w') as file:
            json.dump((self.converted_values(), self.metadata()), file)
