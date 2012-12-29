__author__ = 'lene'

from functools import update_wrapper

def decorator(d):
    "Make function d a decorator: d wraps a function fn."
    def _d(fn):
        return update_wrapper(d(fn), fn)
    update_wrapper(_d, d)
    return _d

@decorator
def memo(f):
    """Decorator that caches the return value for each call to f(args).
    Then when called again with same args, we can just look it up."""
    cache = {}
    def _f(*args):
        try:
            if not args in cache:
                cache[args] = f(*args)
            return cache[args]
        except TypeError:
            # some element of args can't be a dict key
            return f(args)
    return _f
