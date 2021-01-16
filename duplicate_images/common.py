__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path


def path_with_parent(path: Path) -> str:
    return '/'.join(str(path).split('/')[-2:])
