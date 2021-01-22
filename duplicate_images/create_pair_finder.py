__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import List, Optional

from duplicate_images.cache_decorator import CacheDecorator
from duplicate_images.function_types import Cache, HashFunction
from duplicate_images.image_pair_finder import ImagePairFinder, ParallelImagePairFinder
from duplicate_images.pair_finder_interface import PairFinderInterface
from duplicate_images.parallel_options import ParallelOptions


def create_pair_finder(
        files: List[Path], hash_algorithm: HashFunction,
        parallel_options: ParallelOptions, show_progress_bar: bool = False,
        hash_store: Optional[Cache] = None
) -> PairFinderInterface:
    if parallel_options.parallel:
        pair_finder: PairFinderInterface = ParallelImagePairFinder(
            files, hash_algorithm, parallel_options, show_progress_bar
        )
    else:
        pair_finder = ImagePairFinder(files, hash_algorithm, show_progress_bar)
    if hash_store is not None:
        pair_finder = CacheDecorator(pair_finder, hash_store)
    return pair_finder
