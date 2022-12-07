# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Support for Sphinx style reST docs to doc parse.
- Optional `name` argument to [tanchan.docs_parse.as_slash_command][] which
  allows overriding the command's name.

### Fixed
- [tanchan.doc_parse.as_slash_command][] no-longer errors when the callback's
  docstring is just the description and `doc_style` is [None][].
- [tanjun.doc_parse.with_annotated_args][] now allows [None][] to be explicitly
  passed to `doc_style` typing wise.

## [0.1.0] - 2022-12-02
### Added
- An extension to [tanjun.annotations][] which allows for parsing slash command
  descriptions (including for options) from the command callback's docstring +
  using the callback's name as the command's name.

[Unreleased]: https://github.com/FasterSpeeding/tanchan/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/FasterSpeeding/tanchan/compare/c4525eb9271445d3c74dbe747952faf2c830716b...v0.1.0
