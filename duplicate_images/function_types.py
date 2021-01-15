__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

AlgorithmOptions = Dict[str, float]
ComparisonFunction = Callable[[Path, Path, AlgorithmOptions], bool]
ActionFunction = Callable[[Tuple[Path, Path]], Any]
Results = List[Tuple[Path, Path]]
