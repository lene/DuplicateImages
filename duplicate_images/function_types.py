"""
Shorter and more descriptive type aliases used in static type checking for the
`duplicate_images` package.
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from argparse import Namespace
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Generator

from PIL import Image
from imagehash import ImageHash

HashFunction = Callable[[Image.Image], ImageHash]
ImageGroup = Tuple[Path, ...]
ActionFunction = Callable[[Namespace, ImageGroup], Any]
Results = List[ImageGroup]
ResultsGenerator = Generator[List[Path], None, None]
ResultsGrouper = Callable[[ResultsGenerator], Results]
CacheEntry = Tuple[Path, Optional[ImageHash]]
Cache = Dict[Path, ImageHash]
