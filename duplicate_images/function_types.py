__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from PIL import Image
from imagehash import ImageHash


HashFunction = Callable[[Image.Image], ImageHash]
ActionFunction = Callable[[Tuple[Path, Path]], Any]
Results = List[Tuple[Path, Path]]
CacheEntry = Tuple[Path, Optional[ImageHash]]
Cache = Dict[Path, ImageHash]
ImagePair = Tuple[Path, Path]
