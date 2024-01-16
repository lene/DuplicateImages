# Changelog

## [0.10.8] - 2024-01-16

### Added
- optional argument to specify the number of threads with `--parallel`
- `--parallel-actions` option to run actions in parallel
- performance optimization when reading the files to compare

## [0.10.7] - 2024-01-13

### Added
- Check that `hash_size` ia a power of 2 for `whash` algorithm

## [0.10.6] - 2024-01-12

### Fixed
- Python 3.12 compatibility
- bugfix: guard against OS failures when determining file type
- small memory optimization

## [0.10.5] - 2024-01-12

### Added
- `--exclude-dir` option to exclude directories from scanning
- `--max-image-pixels` option to allow for huge images to bypass `PIL`'s `DecompressionBombError`

## [0.10.4] - 2024-01-11

### Fixed
- Upgrade dependencies to fix security vulnerabilities

## [0.10.3] - 2023-10-05
- Changes to CI only

## [0.10.2] - 2023-10-05

### Fixed
- Upgrade Pillow dependency to 10.0.1 to fix libWebP security vulnerability
- Upgrade GitPython dependency to 3.1.37 to fix security vulnerability

## [0.10.1] - 2023-09-04

### Added
- Upgrade Python dependency to 3.9 to fix security warning about old SciPy version
- create GitLab release automatically for each new tag

### Fixed
- create GitHub release from the correct state

## [0.10.0] - 2023-09-03

### Added
- Store hashing algorithm and parameters in hash-db file to ensure that the same algorithm is used 
  across separate runs with the same hash-db file

### Changed
- Breaking change in the hash-db file format - files from previous versions are not compatible

## [0.9.2] - 2023-08-26

### Added
- `symlink-smaller` action to replace the smaller files of a group with a symlink to the biggest one

### Changed
- `delete-smaller` and `delete-bigger` actions to `delete-smallest` and `delete-biggest`

## [0.9.1] - 2023-08-23

### Added
- add documentation for new `--group` option

## [0.9.0] - 2023-08-23

### Added 
- CLI option `--group`: instead of pairs, treat similar images as groups of arbitrary size
- refactor `ImagePairFinder` to easier deal with combinations of options
- test coverage for all supported combinations of `--group`/`--parallel`

## [0.8.9] - 2023-08-23

### Added 
- create GitHub release automatically for each new tag
- updated and completed developer documentation

## [0.8.8] - 2023-08-23

### Added 
- more info in log about runtime and warn about bad decisions

## [0.8.7] - 2023-08-22

### Added 
- run bandit SAST scanner in CI and on every push
- fixed some security warnings, intentionally ignored others
- run GitHub dependency scan in GitHub CI on every merge to master and weekly

## [0.8.6] - 2023-08-22

### Added 
- Changelog

## [0.8.5] - 2023-08-21

### Added 
- log execution times for scanning and comparing
- code reorganization

### Changed
- renamed `--serial` option to `--slow`

## [0.8.4] - 2023-08-21

### Fixed
- removed an absolute path in test suite

## [0.8.3] - 2023-08-21

### Added 
- updated dependencies to newest versions
- upped Development Status in metadata to Beta

### Removed
- support for Python 3.7

## [0.8.2] - 2023-08-21

### Added 
- JSON file format for the image hash persistent store

## [0.8.1] - 2023-08-15

### Added
- test WEBP and HEIC image formats

## [0.8.0] - 2023-08-11

### Added 
- change algorithm to run in O(N) instead of O(N^2) by using the image hashes as dict keys
  - old algorithm still runs if using `--max-distance` switch
- add `--serial` CLI switch to explicitly select old algorithm
- test run script in CI with most relevant CLI parameter combinations

### Removed
- `pre-commit` since it causes more trouble than it's worth

## [0.7.4] - 2023-08-10

### Added 
- experiment with `pre-commit` to run commit hooks in a more standardized way 

## [0.7.3] - 2023-08-10

### Added 
- more pedantic linting and tests on all supported Python versions in CI
- add MIT license file

## [0.7.1] - 2023-02-03

### Added
- contributed by [@mreiche](https://github.com/mreiche): support for running any command passed by 
 `--on-equal`
- contributed by [@mreiche](https://github.com/mreiche): faster MIME detection
- contributed by [@mreiche](https://github.com/mreiche): `print_inline` and `quote_inline` actions

## [0.6.5] - 2023-01-02

### Added 
- contributed by [@beijingjazzpanda](https://gitlab.com/beijingjazzpanda): ensure hash-db `.bak` 
  files are created properly
- run Codacy and CodeQL security and dependency scans in CI on GitHub

## [0.6.4] - 2022-09-23

### Added 
- `--hash-size` option to fine tune which images are considered equal
- support new `dhash_vertical` and `phash_simple` image hashing methods
- push to GitHub repository from CI when MR is merged

## [0.6.2] - 2022-09-04

### Added 
- code style: enforce single quotes as default

## [0.6.1] - 2022-09-02

### Added
- `--max-distance` option to fine tune which images are considered equal

## [0.6.0] - 2022-07-22

### Added 
- support HEIC images
- fix dependabot alerts for insecure dependencies

## [0.5.3] - 2021-03-16

### Added 
- add `--quiet` flag to decrease log level

## [0.5.2] - 2021-03-16

### Added 
- add `d1` and `d2` action shortcuts

## [0.5.1] - 2021-03-15

### Added 
- update documentation for new `--hash-db` CLI parameter

## [0.5.0] - 2021-03-15

### Added 
- store the image hashes in a pickle file between runs for a major speedup
- run tests in parallel

## [0.4.1] - 2021-01-17

### Added
- display a progress bar while calculating

## [0.4.0] - 2021-01-16

### Added 
- automatically publish to PyPI from CI when MR is merged
- reorganize code

## [0.3.6] - 2021-01-16

### Added 
- update homepage and description in project metadata

## [0.3.5] - 2021-01-16

### Added 
- change master repository to https://github.com/lene/DuplicateImages.git

## [0.3.4] - 2021-01-16

### Added 
- improve log formatting
- add option to print matching files with quotes, as well as `d>` and `d<` shortcuts

## [0.3.2] - 2021-01-16

### Added 
- use `coloredlogs` and improve log formatting

## [0.3.1] - 2021-01-16

### Added 
- handle error for broken image files
- use `logging` instead of `print()` for output

## [0.3.0] - 2021-01-16

### Added 
- actions to delete bigger/smaller image and view with `eog`
- fuzziness parameter to adjust desired similarity

## [0.2.1] - 2021-01-15

### Added 
- documentation for parallel execution

## [0.2.0] - 2021-01-15

### Added
- additionally use [ImageHash](https://pypi.org/project/ImageHash) to compare images
- run `pylint` against code
 
## 0.1 - 2021-01-08

### Added
- exact and histogram comparison
- actions if equal: delete one of the pics, view with `xv` or print


[0.10.8]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.10.7...0.10.8
[0.10.7]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.10.6...0.10.7
[0.10.6]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.10.5...0.10.6
[0.10.5]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.10.4...0.10.5
[0.10.4]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.10.3...0.10.4
[0.10.3]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.10.2...0.10.3
[0.10.2]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.10.1...0.10.2
[0.10.1]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.10.0...0.10.1
[0.10.0]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.9.2...0.10.0
[0.9.2]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.9.1...0.9.2
[0.9.1]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.9.0...0.9.1
[0.9.0]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.8.9...0.9.0
[0.8.9]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.8.8...0.8.9
[0.8.8]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.8.7...0.8.8
[0.8.7]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.8.6...0.8.7
[0.8.6]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.8.5...0.8.6
[0.8.5]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.8.4...0.8.5
[0.8.4]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.8.3...0.8.4
[0.8.3]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.8.2...0.8.3
[0.8.2]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.8.1...0.8.2
[0.8.1]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.8.0...0.8.1
[0.8.0]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.7.4...0.8.0
[0.7.4]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.7.3...0.7.4
[0.7.3]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.7.1...0.7.3
[0.7.1]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.6.5...0.7.1
[0.6.5]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.6.4...0.6.5
[0.6.4]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.6.2...0.6.4
[0.6.2]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.6.1...0.6.2
[0.6.1]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.6.0...0.6.1
[0.6.0]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.5.3...0.6.0
[0.5.3]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.5.2...0.5.3
[0.5.2]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.5.1...0.5.2
[0.5.1]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.5.0...0.5.1
[0.5.0]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.4.1...0.5.0
[0.4.1]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.4.0...0.4.1
[0.4.0]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.3.6...0.4.0
[0.3.6]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.3.5...0.3.6
[0.3.5]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.3.4...0.3.6
[0.3.4]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.3.2...0.3.4
[0.3.2]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.3.1...0.3.2
[0.3.1]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.3.0...0.3.1
[0.3.0]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.2.1...0.3.0
[0.2.1]: https://gitlab.com/duplicateimages/DuplicateImages/-/compare/0.2.0...0.2.1
[0.2.0]: https://gitlab.com/duplicateimages/DuplicateImages/-/tags/0.2.0
