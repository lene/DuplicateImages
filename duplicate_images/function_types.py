"""
Shorter and more descriptive type aliases used in static type checking for the
`duplicate_images` package.
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from argparse import Namespace
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Generator, Union

from PIL import Image
from imagehash import ImageHash, ImageMultiHash

Hash = Union[ImageHash, ImageMultiHash]
HashFunction = Callable[[Image.Image], Hash]
ImageGroup = Tuple[Path, ...]
ActionFunction = Callable[[Namespace, ImageGroup], Any]
Results = List[ImageGroup]
ResultsGenerator = Generator[List[Path], None, None]
ResultsGrouper = Callable[[ResultsGenerator], Results]
CacheEntry = Tuple[Path, Optional[Hash]]
CacheKey = Tuple[Path, float, int]  # (path, mtime, size)
Cache = Dict[CacheKey, Hash]


def is_hash(x: Any) -> bool:
    return isinstance(x, (ImageHash, ImageMultiHash))
