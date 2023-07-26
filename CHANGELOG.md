# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
## [0.3.1] - 2023-07-26
### Added
- Support for the application command `nsfw` config option.

### Changed
- Bumped the minimum Tanjun version to `2.16.0`.

## [0.3.0] - 2023-03-12
### Changed
- [with_annotated_args][tanchan.doc_parse.with_annotated_args] will now also parse
  option descriptions from the docstring of the typed dict being used as an
  unpacked `**kwargs` type hint.

## [0.2.2.post] - 2023-03-04
### Fixed
- [SlashCommandGroup.as_sub_command][tanchan.doc_parse.SlashCommandGroup.as_sub_command]
  now actually adds the created command to the group.

## [0.2.2] - 2023-03-03
### Added
- Extended [tanjun.SlashCommandGroup][] impl at [tanchan.doc_parse.SlashCommandGroup][]
  where the `name`, and `description` parameters are now optional and introspected from
  the callback's docstring by default for
  [SlashCommandGroup.as_sub_command][tanchan.doc_parse.SlashCommandGroup.as_sub_command].
  [SlashCommandGroup.make_sub_group][tanchan.doc_parse.SlashCommandGroup.make_sub_group]
  also returns a [tanchan.doc_parse.SlashCommandGroup][] instance.
- Optional `description` arg to [tanchan.doc_parse.as_slash_command][] to allow
  overriding the introspected value.

### Changed
- [tanchan.doc_parse.as_slash_command][] is now typed to allow decorating
  commands which match the abstract types in [tanjun.abc][], not just the
  standard impls.
- A mapping of locales to values can now be passed for `name` to
  [tanchan.doc_parse.as_slash_command][].

## [0.2.1] - 2023-02-01
### Changed
- Bumped the minimum Tanjun version to `v2.11.3`.
- Updated the type-hints for [tanchan.doc_parse.as_slash_command][] to match
  changes to Tanjun.

## [0.2.0] - 2022-12-07
### Added
- Support for Sphinx style reST docs to doc parse.
- Optional `name` argument to [tanchan.doc_parse.as_slash_command][] which
  allows overriding the command's name.

### Fixed
- [tanchan.doc_parse.as_slash_command][] no-longer errors when the callback's
  docstring is just the description and `doc_style` is [None][].
- [tanchan.doc_parse.with_annotated_args][] now allows [None][] to be explicitly
  passed to `doc_style` typing wise.

## [0.1.0] - 2022-12-02
### Added
- An extension to [tanjun.annotations][] which allows for parsing slash command
  descriptions (including for options) from the command callback's docstring +
  using the callback's name as the command's name.

[Unreleased]: https://github.com/FasterSpeeding/tanchan/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/FasterSpeeding/tanchan/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/FasterSpeeding/tanchan/compare/v0.2.2.post...v0.3.0
[0.2.2.post]: https://github.com/FasterSpeeding/tanchan/compare/v0.2.2...v0.2.2.post
[0.2.2]: https://github.com/FasterSpeeding/tanchan/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/FasterSpeeding/tanchan/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/FasterSpeeding/tanchan/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/FasterSpeeding/tanchan/compare/c4525eb9271445d3c74dbe747952faf2c830716b...v0.1.0
