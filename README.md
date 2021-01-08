DuplicateImages
===============

Finds equal or similar images in a directory containing (many) image files.

Needs Python3 and Pillow imaging library to run, additionally Wand for the test suite.

Running
-------
```shell
$ python3 duplicate.py $PICTURE_DIR
```
or
```shell
$ python3 duplicate.py -h
```
for a list of all possible options.

Testing
-------
Prerequisites:
```shell
$ pip install mypy flake8 pytest wand 
```
Running:
```shell
$ mypy .
$ flake8 .
$ pytest
```