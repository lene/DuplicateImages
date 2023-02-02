__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import logging
from argparse import Namespace

import coloredlogs


def setup_logging(args: Namespace) -> None:
    log_level = logging.DEBUG if args.debug else logging.INFO
    for _ in range(args.quiet):
        log_level += (logging.INFO - logging.DEBUG)
    coloredlogs.install(
        level=log_level, fmt='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
