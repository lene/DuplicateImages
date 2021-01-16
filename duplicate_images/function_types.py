__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import Any, Callable, List, Tuple
from PIL import Image

HashFunction = Callable[[Image.Image], int]
ActionFunction = Callable[[Tuple[Path, Path]], Any]
Results = List[Tuple[Path, Path]]
