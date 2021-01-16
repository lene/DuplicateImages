__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from dataclasses import dataclass


@dataclass
class ParallelOptions:
    parallel: bool = False
    chunk_size: int = 0
