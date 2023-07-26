# -*- coding: utf-8 -*-
# BSD 3-Clause License
#
# Copyright (c) 2022-2023, Faster Speeding
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""[tanjun.annotations][] extension which uses docstring parsing."""
from __future__ import annotations as _

__all__: list[str] = ["SlashCommandGroup", "as_slash_command", "slash_command_group", "with_annotated_args"]

import re
import typing

import tanjun
import typing_extensions

from ._internal import inspect

if typing.TYPE_CHECKING:
    from collections import abc as collections

    import hikari

    _AnyCallbackSigT = typing.TypeVar("_AnyCallbackSigT", bound=collections.Callable[..., typing.Any])
    _AnyCommandT = typing.Union[
        tanjun.abc.MenuCommand[_AnyCallbackSigT, typing.Any],
        tanjun.abc.MessageCommand[_AnyCallbackSigT],
        tanjun.abc.SlashCommand[_AnyCallbackSigT],
    ]
    _CallbackishT = typing.Union["_SlashCallbackSigT", _AnyCommandT["_SlashCallbackSigT"]]
    _CommandUnionT = typing.TypeVar(
        "_CommandUnionT", bound=typing.Union[tanjun.SlashCommand[typing.Any], tanjun.MessageCommand[typing.Any]]
    )
    _SlashCallbackSigT = typing.TypeVar("_SlashCallbackSigT", bound=tanjun.abc.SlashCallbackSig)

    # While these overloads may seem redundant/unnecessary, MyPy cannot understand
    # this when expressed through `callback: _CallbackIshT[_SlashCallbackSigT]`.
    class _AsSlashResultProto(typing.Protocol):
        @typing.overload
        def __call__(self, _: _SlashCallbackSigT, /) -> tanjun.SlashCommand[_SlashCallbackSigT]:
            ...

        @typing.overload
        def __call__(self, _: _AnyCommandT[_SlashCallbackSigT], /) -> tanjun.SlashCommand[_SlashCallbackSigT]:
            ...


def _make_slash_command(
    callback: _CallbackishT[_SlashCallbackSigT],
    /,
    *,
    always_defer: bool,
    default_member_permissions: typing.Union[hikari.Permissions, int, None] = None,
    default_to_ephemeral: typing.Optional[bool],
    description: typing.Union[str, collections.Mapping[str, str], None] = None,
    dm_enabled: typing.Optional[bool] = None,
    is_global: bool = True,
    name: typing.Union[str, collections.Mapping[str, str], None],
    nsfw: bool = False,
    sort_options: bool,
    validate_arg_keys: bool,
) -> tanjun.SlashCommand[_SlashCallbackSigT]:
    if isinstance(callback, (tanjun.abc.MenuCommand, tanjun.abc.MessageCommand, tanjun.abc.SlashCommand)):
        wrapped_command = callback
        callback = callback.callback

    else:
        wrapped_command = None

    if description is None:
        doc_string = inspect.getdoc(callback)
        if not doc_string:
            raise ValueError("Callback has no doc string")

        description = doc_string.split("\n", 1)[0].strip()

    if name is None:
        name = callback.__name__

    return tanjun.SlashCommand(
        callback,
        name,
        description,
        always_defer=always_defer,
        default_member_permissions=default_member_permissions,
        default_to_ephemeral=default_to_ephemeral,
        dm_enabled=dm_enabled,
        is_global=is_global,
        nsfw=nsfw,
        sort_options=sort_options,
        validate_arg_keys=validate_arg_keys,
        _wrapped_command=wrapped_command,
    )


def as_slash_command(
    *,
    always_defer: bool = False,
    default_member_permissions: typing.Union[hikari.Permissions, int, None] = None,
    default_to_ephemeral: typing.Optional[bool] = None,
    description: typing.Union[str, collections.Mapping[str, str], None] = None,
    dm_enabled: typing.Optional[bool] = None,
    is_global: bool = True,
    name: typing.Union[str, collections.Mapping[str, str], None] = None,
    nsfw: bool = False,
    sort_options: bool = True,
    validate_arg_keys: bool = True,
) -> _AsSlashResultProto:
    r"""Build a [tanjun.SlashCommand][] by decorating a function.

    This uses the function's name as the command's name and the first line of
    its docstring as the command's description.

    !!! note
        Under the standard implementation, `is_global` is used to determine whether
        the command should be bulk set by
        [Client.declare_global_commands][tanjun.abc.Client.declare_global_commands]
        or when `declare_global_commands` is True

    !!! warning
        `default_member_permissions`, `dm_enabled` and `is_global` are
        ignored for commands within slash command groups.

    !!! note
        If you want your first response to be ephemeral while using
        `always_defer`, you must set `default_to_ephemeral` to `True`.

    Examples
    --------
    ```py
    --8<-- "./docs_src/doc_parse.py:24:30"
    ```

    Parameters
    ----------
    always_defer
        Whether the contexts this command is executed with should always be deferred
        before being passed to the command's callback.
    default_member_permissions
        Member permissions necessary to utilize this command by default.

        If this is [None][] then the configuration for the parent component or client
        will be used.
    default_to_ephemeral
        Whether this command's responses should default to ephemeral unless flags
        are set to override this.

        If this is left as [None][] then the default set on the parent command(s),
        component or client will be in effect.
    dm_enabled
        Whether this command is enabled in DMs with the bot.

        If this is [None][] then the configuration for the parent component or client
        will be used.
    is_global
        Whether this command is a global command.
    name
        The command's name.

        This must fit [discord's requirements](https://discord.com/developers/docs/interactions/application-commands#application-command-object-application-command-naming)
        and if left as [None][] then the command callback's name is used.
    nsfw
        Whether this command should only be accessible in channels marked as
        nsfw.
    sort_options
        Whether this command should sort its set options based on whether
        they're required.

        If this is [True][] then the options are re-sorted to meet the requirement
        from Discord that required command options be listed before optional
        ones.
    validate_arg_keys
        Whether to validate that option keys match the command callback's signature.

    Returns
    -------
    collections.abc.Callable[[tanjun.abc.SlashCallbackSig], SlashCommand]
        The decorator callback used to make a [tanjun.SlashCommand][].

        This can either wrap a raw command callback or another callable command instance
        (e.g. [tanjun.MenuCommand][], [tanjun.MessageCommand][] [tanjun.SlashCommand][])
        and will manage loading the other command into a component when using
        [Component.load_from_scope][tanjun.components.Component.load_from_scope].

    Raises
    ------
    ValueError
        Raises a value error for any of the following reasons:

        * If the command name is over 32 characters long.
        * If the command name has uppercase characters.
        * If the description is over 100 characters long.
    """  # noqa: D202, E501

    def decorator(callback: _CallbackishT[_SlashCallbackSigT], /) -> tanjun.SlashCommand[_SlashCallbackSigT]:
        return _make_slash_command(
            callback,
            always_defer=always_defer,
            default_member_permissions=default_member_permissions,
            default_to_ephemeral=default_to_ephemeral,
            description=description,
            dm_enabled=dm_enabled,
            is_global=is_global,
            name=name,
            nsfw=nsfw,
            sort_options=sort_options,
            validate_arg_keys=validate_arg_keys,
        )

    return decorator


def _line_empty(line: str, /) -> bool:
    return not line.strip()


def _terminate_line(descriptions: dict[str, str], current_line: list[str], /) -> None:
    if current_line:
        name = current_line.pop(0)
        descriptions[name] = " ".join(current_line)
        current_line.clear()


class _Descriptions:
    __slots__ = ("descriptions", "regex")

    def __init__(self, regex: re.Pattern[str], /) -> None:
        self.descriptions: dict[str, str] = {}
        self.regex = regex

    def collect(self, lines: collections.Iterable[str], /) -> None:
        current_line: list[str] = []
        for line in lines:
            result = self.regex.search(line)
            if not result:
                current_line.append(line.strip())
                continue

            _terminate_line(self.descriptions, current_line)
            groups = result.groups()
            current_line.append(groups[0])
            if len(groups) > 1 and (description := groups[1].strip()):
                current_line.append(description)

        _terminate_line(self.descriptions, current_line)


# TODO: would dedenting the lines and having ^ at the start here be preferable?
_GOOGLE_PATTERN = re.compile(r"(\w+).*:(.*)$")


def _parse_google(lines: list[str], /) -> dict[str, str]:
    descriptions = _Descriptions(_GOOGLE_PATTERN)
    start_index: typing.Optional[int] = None

    for index, line in enumerate(lines):
        if line.lower().strip() == "args:":
            start_index = index + 1

        if start_index is not None and _line_empty(line):
            descriptions.collect(lines[start_index:index])
            start_index = None

    if start_index is not None:
        descriptions.collect(lines[start_index : len(lines)])

    return descriptions.descriptions


_NUMPY_PATTERN = re.compile(r"^(\w+)(?: *:.+)?$")


def _dedent_lines(lines: list[str], /) -> collections.Iterable[str]:
    indent = lines[0].removesuffix(lines[0].rstrip())
    return (line.removeprefix(indent) for line in lines)


def _parse_numpy(lines: list[str], /) -> dict[str, str]:
    descriptions = _Descriptions(_NUMPY_PATTERN)
    start_index: typing.Optional[int] = None

    for index, line in enumerate(lines):
        try:
            if not line.startswith("-") or line.replace("-", ""):
                continue

            if start_index is None and lines[index - 1].lower().strip() in ("parameters", "other parameters"):
                start_index = index + 1

            elif start_index is not None and not lines[index - 1]:
                descriptions.collect(_dedent_lines(lines[start_index : index - 1]))
                start_index = None

            elif start_index is not None and _line_empty(lines[index - 2]):
                descriptions.collect(_dedent_lines(lines[start_index : index - 2]))
                start_index = None

        except KeyError:
            pass

    if start_index is not None:
        descriptions.collect(lines[start_index : len(lines)])

    return descriptions.descriptions


_REST_PATTERN = re.compile(r"^:(\w+) (\w+):(.*)$")


def _parse_rest(lines: list[str], /) -> dict[str, str]:
    current_line: list[str] = []
    descriptions: dict[str, str] = {}

    for line in lines:
        match = _REST_PATTERN.match(line)
        if not match:  # TODO: does this want to be indentation aware?
            current_line.append(line.strip())
            continue

        category, name, description = match.groups()
        _terminate_line(descriptions, current_line)
        if category != "param":
            continue

        current_line.append(name)
        if description := description.strip():
            current_line.append(description)

    _terminate_line(descriptions, current_line)
    return descriptions


_DocStyleUnion = typing.Literal["google", "numpy", "reST"]
_PARSERS: dict[_DocStyleUnion, collections.Callable[[list[str]], dict[str, str]]] = {
    "google": _parse_google,
    "numpy": _parse_numpy,
    "reST": _parse_rest,
}

_MATCH_STYLE: list[tuple[re.Pattern[str], _DocStyleUnion]] = [
    (re.compile(r"\n[\t ]*args:\n", re.IGNORECASE), "google"),
    (re.compile(r"\n[\t ]*parameters\n[\t ]*-+", re.IGNORECASE), "numpy"),
    (re.compile(r"\n:param \w+:"), "reST"),
]


def _get_docstyle(doc_string: str) -> typing.Optional[_DocStyleUnion]:
    for pattern, style in _MATCH_STYLE:
        if pattern.search(doc_string):
            return style

    return None


def _parse_descriptions(
    callback: collections.Callable[..., typing.Any], /, *, doc_style: typing.Optional[_DocStyleUnion] = None
) -> dict[str, str]:
    if doc_style and doc_style not in _PARSERS:
        raise ValueError(f"Unsupported docstring style {doc_style!r}")

    kwargs: dict[str, typing.Any] = {}
    for parameter in inspect.signature(callback, eval_str=True).parameters.values():
        if parameter.kind is not parameter.VAR_KEYWORD:
            continue

        if typing_extensions.get_origin(parameter.annotation) is not typing_extensions.Unpack:
            break

        typed_dict = typing_extensions.get_args(parameter.annotation)[0]
        if not typing_extensions.is_typeddict(typed_dict):
            break

        if typed_dict_doc := inspect.getdoc(typed_dict):
            typed_dict_doc_style = doc_style or _get_docstyle(typed_dict_doc)
            parser = _PARSERS.get(typed_dict_doc_style) if typed_dict_doc_style else None

            # We don't error when it couldn't detect the style here as this could
            # be inheriting the docstring from another typeddict class.
            if parser:
                kwargs.update(parser(typed_dict_doc.splitlines()))

    if doc_string := inspect.getdoc(callback):
        lines = doc_string.splitlines()[1:]
        if not lines:
            return kwargs

        doc_style = doc_style or _get_docstyle(doc_string)
        if not doc_style:
            if kwargs:
                return kwargs

            raise RuntimeError("Couldn't detect the docstring style")

        kwargs.update(_PARSERS[doc_style](lines))

    elif not kwargs:
        raise ValueError("Callback has no doc string")

    return kwargs


@typing.overload
def with_annotated_args(command: _CommandUnionT, /) -> _CommandUnionT:
    ...


@typing.overload
def with_annotated_args(
    *, doc_style: typing.Optional[_DocStyleUnion] = None, follow_wrapped: bool = False
) -> collections.Callable[[_CommandUnionT], _CommandUnionT]:
    ...


def with_annotated_args(
    command: typing.Optional[_CommandUnionT] = None,
    /,
    *,
    doc_style: typing.Optional[_DocStyleUnion] = None,
    follow_wrapped: bool = False,
) -> typing.Union[_CommandUnionT, collections.Callable[[_CommandUnionT], _CommandUnionT]]:
    r"""Docstring parsing implementation of [tanjun.annotations.with_annotated_args][].

    Examples
    --------

    This will parse command option descriptions from the command's docstring.

    ```py
    --8<-- "./docs_src/doc_parse.py:34:64"
    ```

    This also supports parsing option descriptions from the typed dict that's
    being used as the unpacked `**kwargs` type-hint.

    ```py
    --8<-- "./docs_src/doc_parse.py:68:93"
    ```

    Parameters
    ----------
    command : tanjun.SlashCommand | tanjun.MessageCommand
        The message or slash command to set the arguments for.
    doc_style
        The docstyle to parse slash command option descriptions from.

        This may be either `"google"`, `"numpy"`, or `"reST"`.
        If left as [None][] then this will try to auto-detect the style.
    follow_wrapped
        Whether this should also set the arguments on any other command objects
        this wraps in a decorator call chain.

    Returns
    -------
    tanjun.SlashCommand | tanjun.MessageCommand
        The command object to enable using this as a decorator.

    Raises
    ------
    RuntimeError
        If `doc_style` is [None][] and this failed to detect the docstring style.
    """

    def decorator(command: _CommandUnionT, /) -> _CommandUnionT:
        tanjun.annotations.parse_annotated_args(
            command,
            descriptions=_parse_descriptions(command.callback, doc_style=doc_style),
            follow_wrapped=follow_wrapped,
        )
        return command

    if command:
        return decorator(command)

    return decorator


class SlashCommandGroup(tanjun.SlashCommandGroup):
    """Extended implementation of [tanjun.SlashCommandGroup][] with some doc parsing."""

    __slots__ = ()

    def as_sub_command(
        self,
        name: typing.Union[str, collections.Mapping[str, str], None] = None,
        description: typing.Union[str, collections.Mapping[str, str], None] = None,
        *,
        always_defer: bool = False,
        default_to_ephemeral: typing.Optional[bool] = None,
        sort_options: bool = True,
        validate_arg_keys: bool = True,
    ) -> collections.Callable[[_CallbackishT[_SlashCallbackSigT]], tanjun.SlashCommand[_SlashCallbackSigT]]:
        r"""Build a [tanjun.SlashCommand][] in this command group by decorating a function.

        !!! note
            If you want your first response to be ephemeral while using
            `always_defer`, you must set `default_to_ephemeral` to `True`.

        Parameters
        ----------
        name
            The command's name (supports [localisation](https://tanjun.cursed.solutions/usage/#localisation)).

            If left as [None][] then the command callback's name will be used.

            This must fit [discord's requirements](https://discord.com/developers/docs/interactions/application-commands#application-command-object-application-command-naming).
        description
            The command's description.

            If left as [None][] then the first line of the command callback's
            description will be used.

            This should be inclusively between 1-100 characters in length.
        always_defer
            Whether the contexts this command is executed with should always be deferred
            before being passed to the command's callback.
        default_to_ephemeral
            Whether this command's responses should default to ephemeral unless flags
            are set to override this.

            If this is left as [None][] then the default set on the parent command(s),
            component or client will be in effect.
        sort_options
            Whether this command should sort its set options based on whether
            they're required.

            If this is [True][] then the options are re-sorted to meet the requirement
            from Discord that required command options be listed before optional
            ones.
        validate_arg_keys
            Whether to validate that option keys match the command callback's signature.

        Returns
        -------
        collections.abc.Callable[[tanjun.abc.SlashCallbackSig], SlashCommand]
            The decorator callback used to make a sub-command.

            This can either wrap a raw command callback or another callable command instance
            (e.g. [tanjun.MenuCommand][], [tanjun.MessageCommand][] [tanjun.SlashCommand][]).

        Raises
        ------
        ValueError
            Raises a value error for any of the following reasons:

            * If the command name doesn't fit Discord's requirements.
            * If the command name has uppercase characters.
            * If the description is over 100 characters long.
        """  # noqa: D202, E501

        def decorator(callback: _CallbackishT[_SlashCallbackSigT]) -> tanjun.SlashCommand[_SlashCallbackSigT]:
            return self.with_command(
                _make_slash_command(
                    callback,
                    always_defer=always_defer,
                    default_to_ephemeral=default_to_ephemeral,
                    description=description,
                    name=name,
                    sort_options=sort_options,
                    validate_arg_keys=validate_arg_keys,
                )
            )

        return decorator

    def make_sub_group(
        self,
        name: typing.Union[str, collections.Mapping[str, str]],
        description: typing.Union[str, collections.Mapping[str, str]],
        /,
        *,
        default_to_ephemeral: typing.Optional[bool] = None,
    ) -> SlashCommandGroup:
        r"""Create a sub-command group in this group.

        !!! note
            Unlike message command groups, slash command groups cannot
            be callable functions themselves.

        Parameters
        ----------
        name
            The name of the command group (supports [localisation](https://tanjun.cursed.solutions/usage/#localisation)).

            This must fit [discord's requirements](https://discord.com/developers/docs/interactions/application-commands#application-command-object-application-command-naming).
        description
            The description of the command group.
        default_to_ephemeral
            Whether this command's responses should default to ephemeral unless flags
            are set to override this.

            If this is left as [None][] then the default set on the parent command(s),
            component or client will be in effect.

        Returns
        -------
        SlashCommandGroup
            The created sub-command group.

        Raises
        ------
        ValueError
            Raises a value error for any of the following reasons:

            * If the command name doesn't fit Discord's requirements.
            * If the command name has uppercase characters.
            * If the description is over 100 characters long.
        """  # noqa: E501
        return self.with_command(slash_command_group(name, description, default_to_ephemeral=default_to_ephemeral))


def slash_command_group(
    name: typing.Union[str, collections.Mapping[str, str]],
    description: typing.Union[str, collections.Mapping[str, str]],
    /,
    *,
    default_member_permissions: typing.Union[hikari.Permissions, int, None] = None,
    default_to_ephemeral: typing.Optional[bool] = None,
    dm_enabled: typing.Optional[bool] = None,
    is_global: bool = True,
    nsfw: bool = False,
) -> SlashCommandGroup:
    r"""Create a slash command group.

    !!! note
        Unlike message command groups, slash command groups cannot
        be callable functions themselves.

    !!! warning
        `default_member_permissions`, `dm_enabled` and `is_global` are
        ignored for command groups within other slash command groups.

    !!! note
        Under the standard implementation, `is_global` is used to determine whether
        the command should be bulk set by
        [Client.declare_global_commands][tanjun.abc.Client.declare_global_commands]
        or when `declare_global_commands` is True

    Examples
    --------
    Sub-commands can be added to the created slash command object through
    the following decorator based approach:

    ```python
    --8<-- "./docs_src/doc_parse.py:97:108"
    ```

    Parameters
    ----------
    name
        The name of the command group (supports [localisation](https://tanjun.cursed.solutions/usage/#localisation)).

        This must fit [discord's requirements](https://discord.com/developers/docs/interactions/application-commands#application-command-object-application-command-naming).
    description
        The description of the command group (supports [localisation](https://tanjun.cursed.solutions/usage/#localisation)).

        This should be inclusively between 1-100 characters in length.
    default_member_permissions
        Member permissions necessary to utilize this command by default.

        If this is [None][] then the configuration for the parent component or client
        will be used.
    default_to_ephemeral
        Whether this command's responses should default to ephemeral unless flags
        are set to override this.

        If this is left as [None][] then the default set on the parent command(s),
        component or client will be in effect.
    dm_enabled
        Whether this command is enabled in DMs with the bot.

        If this is [None][] then the configuration for the parent component or client
        will be used.
    is_global
        Whether this command is a global command.
    nsfw
        Whether this command should only be accessible in channels marked as
        nsfw.

    Returns
    -------
    SlashCommandGroup
        The command group.

    Raises
    ------
    ValueError
        Raises a value error for any of the following reasons:

        * If the command name doesn't fit Discord's requirements.
        * If the command name has uppercase characters.
        * If the description is over 100 characters long.
    """  # noqa: E501
    return SlashCommandGroup(
        name,
        description,
        default_member_permissions=default_member_permissions,
        default_to_ephemeral=default_to_ephemeral,
        dm_enabled=dm_enabled,
        is_global=is_global,
        nsfw=nsfw,
    )
