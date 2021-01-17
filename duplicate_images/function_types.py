__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from PIL import Image
from imagehash import ImageHash


HashFunction = Callable[[Image.Image], int]
ActionFunction = Callable[[Tuple[Path, Path]], Any]
Results = List[Tuple[Path, Path]]
CacheEntry = Tuple[Path, Optional[int]]
Cache = Dict[Path, ImageHash]
ImagePair = Tuple[Path, Path]
