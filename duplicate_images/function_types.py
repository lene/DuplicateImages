__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from PIL import Image
from imagehash import ImageHash
from argparse import Namespace

HashFunction = Callable[[Image.Image], ImageHash]
ImagePair = Tuple[Path, Path]
ActionFunction = Callable[[Namespace, ImagePair], Any]
Results = List[ImagePair]
CacheEntry = Tuple[Path, Optional[ImageHash]]
Cache = Dict[Path, ImageHash]
