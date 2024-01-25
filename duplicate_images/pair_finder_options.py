"""
Encapsulates the options for scanning images and detecting duplicates
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from argparse import Namespace
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PairFinderOptions:
    """
    Encapsulates the options for scanning images and detecting duplicates and
    reads them from an `argparse.Namespace` object
    """
    max_distance: int = 0
    hash_size: Optional[int] = None
    show_progress_bars: bool = False
    parallel: Optional[int] = None
    slow: bool = False
    group: bool = False

    @classmethod
    def from_args(cls, args: Namespace):
        return cls(
            args.max_distance, args.hash_size, args.progress, args.parallel, args.slow, args.group
        )
