# Finding Duplicate Images

Finds equal or similar images in a directory containing (many) image files.

Official home page: https://github.com/lene/DuplicateImages

Development page: https://gitlab.com/lilacashes/DuplicateImages

PyPI page: https://pypi.org/project/duplicate-images

## Usage

Installing:
```shell
$ pip install duplicate_images
```

Printing the help screen:
```shell
$ find-dups -h
```

Quick test run:
```shell
$ find-dups $IMAGE_ROOT 
```

Typical usage:
```shell
$ find-dups $IMAGE_ROOT --parallel --progress --hash-db hashes.pickle
```

### Supported image formats

* JPEG and PNG (tested quite thoroughly)
* HEIC (experimental support, tested cursorily only)

### Image comparison algorithms

Use the `--algorithm` option to select how equal images are found. The default algorithm is `phash`.

`ahash`, `colorhash`, `dhash`, `dhash_vertical`, `phash`, `phash_simple`, `whash`: seven different 
image hashing algorithms. See https://pypi.org/project/ImageHash for an introduction on image 
hashing and https://tech.okcupid.com/evaluating-perceptual-image-hashes-okcupid for some gory 
details which image hashing algorithm performs best in which situation. For a start I recommend 
using `phash`, and only evaluating the other algorithms if `phash` does not perform satisfactorily 
in your use case.

### Image similarity threshold configuration

Use the `--max-distance` parameter to tune how close images should be to be considered duplicates.
The argument is a positive integer. Its value is highly dependent on the algorithm used and the 
nature of the images compared, so the best value for your use case can oly be found through 
experimentation.

Use the `--hash-size` parameter to tune the precision of the hashing algorithms. For the `colorhash`
algorithm the hash size is interpreted as the number of bin bits and defaults to 3. For all other
algorithms the hash size defaults to 8. For `whash` it must be a power of 2.

### Actions for matching image pairs

Use the `--on-equal` option to select what to do to pairs of equal images. The default action is 
`print`.
- `delete-first` or `d1`: deletes the first of the two files
- `delete-second` or `d2`: deletes the second of the two files
- `delete-bigger` or `d>`: deletes the file with the bigger size
- `delete-smaller` or `d<`: deletes the file with the smaller size
- `eog`: launches the `eog` image viewer to compare the two files
- `xv`: launches the `xv` image viewer to compare the two files
- `print`: prints the two files
- `quote`: prints the two files with quotes around each 
- `none`: does nothing.
  
### Parallel execution

Use the `--parallel` option to utilize all free cores on your system. 

### Progress and verbosity control

- `--progress` prints a progress bar each for the process of reading the images, and the process of 
  finding duplicates among the scanned image
- `--debug` prints debugging output
- `--quiet` decreases the log level by 1 for each time it is called; `--debug` and `--quiet` cancel
  each other out

### Pre-storing and using image hashes to speed up computation

Use the `--hash-db $PICKLE_FILE` option to store image hashes in the file `$PICKLE_FILE` and read
image hashes from that file if they are already present there. This avoids having to compute the 
image hashes anew at every run and can significantly speed up run times.

## Development notes

Needs Python3, Pillow imaging library and `pillow-heif` HEIF plugin to run, additionally Wand for 
the test suite.

Uses Poetry for dependency management.

### Installation

From source:
```shell
$ git clone https://gitlab.com/lilacashes/DuplicateImages.git
$ cd DuplicateImages
$ pip3 install poetry
$ poetry install
```

### Running

```shell
$ poetry run find-dups $PICTURE_DIR
```
or
```shell
$ poetry run find-dups -h
```
for a list of all possible options.

### Test suite

Running it all:
```shell
$ poetry run pytest
$ poetry run mypy duplicate_images tests
$ poetry run flake8
$ poetry run pylint duplicate_images tests
```
or simply 
```shell
$ .git_hooks/pre-push
```
Setting the test suite to be run before every push:
```shell
$ cd .git/hooks
$ ln -s ../../.git_hooks/pre-push .
```

### Publishing

There is a job in GitLab CI for publishing to `pypi.org` that runs as soon as a new tag is added. 
The tag needs to be the same as the `version` in the `pyproject.toml` file or else the job will 
fail.

To publish the package on PyPI manually:
```shell
$ poetry config repositories.testpypi https://test.pypi.org/legacy/
$ poetry build
$ poetry publish --username $PYPI_USER --password $PYPI_PASSWORD --repository testpypi && \
  poetry publish --username $PYPI_USER --password $PYPI_PASSWORD
```
(obviously assuming that username and password are the same on PyPI and TestPyPI)

#### Updating GitHub mirror

GitHub is set up as a push mirror in GitLab CI, but mirroring is flaky at the time and may not
succeed. 

To push to the GitHub repository manually (assuming the GitHub repository is set up as remote 
`github`):
```shell
$ git checkout master
$ git fetch
$ git pull --rebase
$ git tag  # to check that the latest tag is present
$ git push --tags github master 
```

### Profiling

#### CPU time
To show the top functions by time spent, including called functions:
```shell
$ poetry run python -m cProfile -s tottime ./duplicate_images/duplicate.py \ 
    --algorithm $ALGORITHM --action-equal none $IMAGE_DIR 2>&1 | head -n 15
```
or, to show the top functions by time spent in the function alone:
```shell
$ poetry run python -m cProfile -s cumtime ./duplicate_images/duplicate.py \ 
    --algorithm $ALGORITHM --action-equal none $IMAGE_DIR 2>&1 | head -n 15
```

#### Memory usage
```shell
$ poetry run fil-profile run ./duplicate_images/duplicate.py \
    --algorithm $ALGORITHM --action-equal none $IMAGE_DIR 2>&1
```
This will open a browser window showing the functions using the most memory (see 
https://pypi.org/project/filprofiler for more details).