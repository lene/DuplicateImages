"""
Functions used in multiple places
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from functools import wraps
from pathlib import Path
from time import time


def path_with_parent(path: Path) -> str:
    return '/'.join(str(path).rstrip('/').split('/')[-2:])


def log_execution_time():
    def actual_decorator(method):
        @wraps(method)
        def allow_fail(self, *args, **kwargs):
            start_time = time()
            return_value = method(self, *args, **kwargs)
            logging.info(
                '%s.%s() run in %.2fs',
                type(self).__name__, method.__name__,
                time() - start_time
            )
            return return_value

        return allow_fail

    return actual_decorator
