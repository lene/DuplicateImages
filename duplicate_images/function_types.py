__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import Any, Callable, Tuple

ComparisonFunction = Callable[[Path, Path, float, float], bool]
ActionFunction = Callable[[Tuple[Path, Path]], Any]
