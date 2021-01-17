__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
import pickle
from pathlib import Path
from typing import Any, Optional, Union

from duplicate_images.function_types import Cache


class NullHashStore:

    def __init__(self) -> None:
        logging.info('No persistent storage for calculated image hashes set up')

    def __enter__(self) -> Cache:
        return {}

    def __exit__(self, _: Any, __: Any, ___: Any) -> None:
        pass


class HashStore:

    @classmethod
    def create(cls, store_path: Optional[Path]) -> Union['HashStore', NullHashStore]:
        return HashStore(store_path) if store_path is not None else NullHashStore()

    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self.values: Cache = {}
        try:
            with store_path.open('rb') as file:
                self.values = pickle.load(file)
            logging.info(
                'Opened persistent storage %s with %d entries', store_path, len(self.values)
            )
        except (FileNotFoundError, pickle.PickleError):
            logging.info('Creating new persistent storage at %s', store_path)
            self.stored_values = {}

    def __enter__(self) -> Cache:
        return self.values

    def __exit__(self, _: Any, __: Any, ___: Any) -> None:
        if self.store_path.is_file():
            self.store_path.rename(self.store_path.with_suffix('.bak'))
        with self.store_path.open('wb') as file:
            pickle.dump(self.values, file)
