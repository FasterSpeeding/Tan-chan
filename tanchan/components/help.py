# -*- coding: utf-8 -*-
# BSD 3-Clause License
#
# Copyright (c) 2023-2024, Faster Speeding
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
"""A components powered help command."""
from __future__ import annotations

__all__: list[str] = ["load_help", "unload_help"]

import hashlib
import inspect
import itertools
import math
import typing
from typing import Annotated

import alluka
import hikari
import tanjun
import yuyo
from tanjun.annotations import Positional
from tanjun.annotations import Str

from .. import _internal
from .. import doc_parse
from . import buttons
from . import config

if typing.TYPE_CHECKING:
    from collections import abc as collections

_CommandT = typing.TypeVar("_CommandT", bound=tanjun.abc.ExecutableCommand[typing.Any])

_IDENTIFIER = "tanchan.help"
"""Identifier used for help components."""

_DEFAULT_CONFIG = config.HelpConfig()

_CATEGORY_KEY = "TANCHAN_HELP_CATEGORY"
"""Key used for overriding a command's category through its metadata."""

_DESCRIPTION_KEY = "TANCHAN_HELP_DESCRIPTIOn"
"""Key used for overriding a command's description through its metadata."""

_INCLUDE_KEY = "TANCHAN_HELP_INCLUDE"
"""Key used to mark whether a command should be included in Tanchan's help response.

Defaults to [True][] for message commands and [False][] for slash commands.
"""

# TODO: improve help command formatting
# TODO: maybe experiment with including command signatures in responses

INDEX_ID = "tan-chan.components.help"


def with_help(
    description: typing.Union[str, collections.Mapping[str, str], None] = None,
    /,
    *,
    category: typing.Optional[str] = None,
    follow_wrapped: bool = False,
) -> collections.Callable[[_CommandT], _CommandT]:
    """Override the help string for the command.

    Parameters
    ----------
    description
        Description to set for the command.

        This supports Tanjun's
        [localisation](https://tanjun.cursed.solutions/usage/#localisation).
    category
        Name of the category this command should be in. Defaults to the
        component's name.
    follow_wrapped
        Whether this should also apply the help information to the other
        command objects this wraps in a decorator call chain.

    Examples
    --------
    ```py
    @hide_from_command("Alternative description.")
    @tanjun.as_message_command("name")
    async def command(ctx: tanjun.abc.Context) -> None:
        ...
    ```
    """

    def set_metadata(cmd: tanjun.abc.ExecutableCommand[typing.Any], /) -> None:
        cmd.metadata[_INCLUDE_KEY] = True
        cmd_name, cmd_type = _to_cmd_info(cmd)
        if description is not None:
            cmd.metadata[_DESCRIPTION_KEY] = _internal.MaybeLocalised(
                "help.description", description, cmd_type=cmd_type, name=cmd_name
            )

        if category is not None:
            cmd.metadata[_CATEGORY_KEY] = category

        _internal.apply_to_wrapped(cmd, set_metadata, follow_wrapped=follow_wrapped)

    def decorator(cmd: _CommandT, /) -> _CommandT:
        set_metadata(cmd)
        return cmd

    return decorator


def _to_cmd_info(cmd: tanjun.abc.ExecutableCommand[typing.Any], /) -> tuple[str, typing.Optional[hikari.CommandType]]:
    """Get the main name and type of a command."""
    if isinstance(cmd, tanjun.abc.AppCommand):
        return cmd.name, cmd.type

    if isinstance(cmd, tanjun.abc.MessageCommand):
        # TODO: upgrade cmd.names to a sequence to insure order
        return tuple(cmd.names)[0], None

    raise NotImplementedError(f"Unsupported command type {type(cmd)}")


@typing.overload
def hide_from_help(cmd: _CommandT, /) -> _CommandT: ...


@typing.overload
def hide_from_help(*, follow_wrapped: bool = False) -> collections.Callable[[_CommandT], _CommandT]: ...


def hide_from_help(
    cmd: typing.Optional[_CommandT] = None, /, *, follow_wrapped: bool = False
) -> typing.Union[_CommandT, collections.Callable[[_CommandT], _CommandT]]:
    """Hide a global command from the help command.

    Parameters
    ----------
    follow_wrapped
        Whether this should also apply the help information to the other
        command objects this wraps in a decorator call chain.

    Examples
    --------
    ```py
    @hide_from_command
    @tanjun.as_message_command("name")
    async def command(ctx: tanjun.abc.Context) -> None:
        '''Meow command.'''
    ```
    """

    def decorator(cmd: _CommandT, /) -> _CommandT:
        cmd.metadata[_INCLUDE_KEY] = False
        _internal.apply_to_wrapped(cmd, hide_from_help, follow_wrapped=follow_wrapped)
        return cmd

    if cmd:
        return decorator(cmd)

    return decorator


def _split_name(name: str, /) -> list[str]:
    """Split a message command name into spaced case-insensitive sections."""
    return name.casefold().split()


class _Page(yuyo.pagination.AbstractPage):
    """Represents a page in the help command's response paginator."""

    __slots__ = ("_category_name", "_fields", "_index", "_page_number")

    def __init__(
        self,
        page_number: int,
        # TODO: can we show sub-pages for the category???
        category_name: _internal.MaybeLocalised,
        fields: list[tuple[str, _internal.MaybeLocalised]],
        /,
    ) -> None:
        """Initialise a help command page.

        Parameters
        ----------
        index
            The help index this is tied to.
        page_number
            This page's 1-indexed position.
        category_name
            Name of the category this page shows the commands from.
        fields
            List of field names ad their descriptions.
        """
        self._category_name = category_name
        self._fields = fields
        self._page_number = page_number

    def _localise(
        self, locale: typing.Optional[hikari.Locale], localiser: typing.Optional[tanjun.dependencies.AbstractLocaliser]
    ) -> tuple[str, str]:
        if locale is None:
            description = "\n".join(f"{name}: " + field.default_value.split("\n", 1)[0] for name, field in self._fields)
            title = f"{self._category_name.default_value} commands"
            return title, description

        description = "\n".join(
            f"{name}: " + field.localise(locale, localiser).split("\n", 1)[0] for name, field in self._fields
        )
        title = self._category_name.localise(locale, localiser)
        return title, description

    def to_content(
        self,
        *,
        locale: typing.Optional[hikari.Locale] = None,
        localiser: typing.Optional[tanjun.dependencies.AbstractLocaliser] = None,
    ) -> str:
        """Create a message content representation of this page.

        Parameters
        ----------
        locale
            Locale to localise this page to, if relevant.
        localiser
            Localiser to use to localise this page, if relevant.

        Returns
        -------
        str
            The message-content friendly string representation of this page.
        """
        title, description = self._localise(locale, localiser)
        return f"```md\n{title}\n{description}\n```"

    def _to_embed(
        self,
        *,
        locale: typing.Optional[hikari.Locale] = None,
        localiser: typing.Optional[tanjun.dependencies.AbstractLocaliser] = None,
    ) -> hikari.Embed:
        """Create a Discord embed representation of this page.

        Parameters
        ----------
        locale
            Locale to localise this page to, if relevant.
        localiser
            Localiser to use to localise this page, if relevant.

        Returns
        -------
        hikari.embeds.Embed
            The Discord embed representation of this page.
        """
        title, description = self._localise(locale, localiser)
        return hikari.Embed(title=title, description=description).set_footer(
            f"Page {self._page_number}/{len(self._index.pages)}"
        )

    def to_kwargs(self) -> yuyo.pagination.ResponseKwargs:
        return {"embeds": [self._to_embed()]}

    def ctx_to_kwargs(
        self,
        ctx: typing.Union[
            yuyo.interactions.BaseContext[hikari.ComponentInteraction],
            yuyo.interactions.BaseContext[hikari.ModalInteraction],
        ],
    ) -> yuyo.pagination.ResponseKwargs:
        localiser = ctx.alluka.get_type_dependency(tanjun.dependencies.AbstractLocaliser)
        permissions = ctx.interaction.app_permissions
        # perms is None indicates a DM where we will always have embed links.
        if permissions is None or permissions & hikari.Permissions.EMBED_LINKS:
            return {"embeds": [self._to_embed(locale=hikari.Locale(ctx.interaction.locale), localiser=localiser)]}

        return {"content": self.to_content(locale=hikari.Locale(ctx.interaction.locale), localiser=localiser)}


def reload(
    _: typing.Optional[tanjun.abc.Component] = None,
    /,
    *,
    client: alluka.Injected[tanjun.abc.Client],
    static_index: alluka.Injected[yuyo.StaticPaginatorIndex],
    help_config: alluka.Injected[config.HelpConfig] = _DEFAULT_CONFIG,
) -> None:
    """Rebuild the help command's index to account for changes."""
    categories: dict[str, list[tuple[str, _internal.MaybeLocalised]]] = {}
    descriptions: dict[tuple[str, ...], _internal.MaybeLocalised] = {}
    pages: list[_Page] = []

    cmds_iter = itertools.chain(
        (_collect_msg_cmds(cmd, help_config) for cmd in client.iter_message_commands()),
        (_collect_slash_cmds(cmd, help_config) for cmd in client.iter_slash_commands()),
    )
    for command, names in itertools.chain.from_iterable(cmds_iter):
        component_name = command.component.name if command.component else "unknown"
        try:
            description_override = command.metadata[_DESCRIPTION_KEY]

        except KeyError:
            description_override = ""

        else:
            if not isinstance(description_override, _internal.MaybeLocalised):
                description_override = None

        cmd_name, cmd_type = _to_cmd_info(command)
        description = inspect.getdoc(command.callback)
        if description_override:
            description = description_override

        elif description:
            description = _internal.MaybeLocalised("help.description", description, cmd_type=cmd_type, name=cmd_name)

        else:
            continue

        # TODO: handle inheriting this state from parent commands
        category = command.metadata.get(_CATEGORY_KEY) or component_name
        if not isinstance(category, str):
            raise TypeError(f"Invalid category name: {category!r}")

        for name in names:
            descriptions[name] = description

        entry = (" ".join(names[0]), description)
        try:
            categories[category].append(entry)

        except KeyError:
            categories[category] = [entry]

    page_number = 0
    for cateory, commands in sorted(categories.items(), key=lambda v: v[0]):
        cateory = _internal.MaybeLocalised("help.category", cateory)
        page_count = math.ceil(len(commands) / 10)
        for index in range(page_count):
            page_number += 1
            pages.append(_Page(page_number, cateory, commands[10 * index : 10 * (index + 1)]))

    items_repr = ((" ".join(k), v.to_hashable()) for k, v in descriptions.items())
    items_repr = ",".join(map(":".join, sorted(items_repr, key=lambda v: v[0]))).encode()
    static_index.set_paginator(
        _IDENTIFIER, pages, content_hash="md5-" + hashlib.md5(items_repr, usedforsecurity=False).hexdigest()
    )
    client.injector.set_type_dependency(CommandDescriptions, CommandDescriptions(descriptions))


class CommandDescriptions:
    __slots__ = ("_descriptions",)

    def __init__(self, descriptions: dict[tuple[str, ...], _internal.MaybeLocalised], /) -> None:
        self._descriptions = descriptions

    def find_command(self, command_name: str, /) -> typing.Optional[_internal.MaybeLocalised]:
        return self._descriptions.get(tuple(_split_name(command_name)))


# TODO: this feels very inefficient
def _collect_msg_cmds(
    command: tanjun.abc.MessageCommand[typing.Any], help_config: config.HelpConfig, /
) -> collections.ItemsView[tanjun.abc.MessageCommand[typing.Any], list[tuple[str, ...]]]:
    results: dict[tanjun.abc.MessageCommand[typing.Any], list[tuple[str, ...]]] = {}

    for names, command in _follow_msg_children(command, help_config):
        names = tuple(names)
        try:
            results[command].append(names)

        except KeyError:
            results[command] = [names]

    return results.items()


def _follow_msg_children(
    command: tanjun.abc.MessageCommand[typing.Any], help_config: config.HelpConfig, /
) -> collections.Iterator[tuple[list[str], tanjun.abc.MessageCommand[typing.Any]]]:
    if command.metadata.get(_INCLUDE_KEY, help_config.include_message_commands):
        yield from ((_split_name(name), command) for name in command.names)

    if isinstance(command, tanjun.abc.MessageCommandGroup):
        commands_iter = itertools.product(
            command.names,
            itertools.chain.from_iterable(_follow_msg_children(cmd, help_config) for cmd in command.commands),
        )
        yield from (([*_split_name(parent_name), *name], command) for parent_name, (name, command) in commands_iter)


def _collect_slash_cmds(
    command: tanjun.abc.BaseSlashCommand, help_config: config.HelpConfig, /
) -> collections.ItemsView[tanjun.abc.SlashCommand[typing.Any], list[tuple[str, ...]]]:
    results: dict[tanjun.abc.SlashCommand[typing.Any], list[tuple[str, ...]]] = {}

    for names, cmd in _follow_slash_children(command, help_config):
        names = tuple(names)
        try:
            results[cmd].append(names)

        except KeyError:
            results[cmd] = [names]

    return results.items()


def _follow_slash_children(
    command: tanjun.abc.BaseSlashCommand, help_config: config.HelpConfig, /
) -> collections.Iterator[tuple[list[str], tanjun.abc.SlashCommand[typing.Any]]]:
    if isinstance(command, tanjun.abc.SlashCommandGroup):
        commands_iter = itertools.chain.from_iterable(
            _follow_slash_children(cmd, help_config) for cmd in command.commands
        )
        yield from (([command.name, *name], sub_command) for (name, sub_command) in commands_iter)

    elif command.metadata.get(_INCLUDE_KEY, help_config.include_slash_commands):
        # Assume this is an actual callable slash command and not a group
        assert isinstance(command, tanjun.abc.SlashCommand)
        yield ([command.name], command)


async def _help_command(
    ctx: typing.Union[tanjun.abc.MessageContext, tanjun.abc.SlashContext],
    *,
    command_name: Annotated[typing.Optional[Str], Positional()] = None,
    command_descriptions: alluka.Injected[CommandDescriptions],
    localiser: alluka.Injected[typing.Optional[tanjun.dependencies.AbstractLocaliser]] = None,
    # TODO: switch cached_inject over to using an injected cache to avoid
    # edge case state issues
    # This could likely also include adding a "ScopedState" return class
    # which lets you scope them per specific resource (e.g. user, member)
    me: hikari.OwnUser = tanjun.cached_inject(tanjun.dependencies.fetch_my_user),
    static_index: alluka.Injected[yuyo.StaticPaginatorIndex],
) -> None:
    """Get information about the bot's commands.

    Parameters
    ----------
    command_name
        Name of a command to get the full information for.
    """
    if isinstance(ctx, tanjun.abc.AppCommandContext):
        locale = hikari.Locale(ctx.interaction.locale)

    else:
        locale = None

    if command_name:
        content = command_descriptions.find_command(command_name)
        components: collections.Sequence[hikari.api.MessageActionRowBuilder] = [buttons.delete_row(ctx.author.id)]

        if not content:
            raise tanjun.CommandError("Couldn't find command", component=buttons.delete_row(ctx.author.id))

        content = content.localise(locale, localiser) if locale else content.default_value
        if await _check_embed_links(ctx, me):
            await ctx.respond(embed=hikari.Embed(description=content), components=components)

        else:
            await ctx.respond(f"```md\n{content}\n```", components=components)

    else:
        paginator = static_index.get_paginator(_IDENTIFIER)
        # TODO: proper intro page + page numbers
        # TODO: it's weird that only the first response for message commands aren't localised
        try:
            page = paginator.get_page(0)

        except IndexError:
            raise tanjun.CommandError("No commands") from None

        assert isinstance(page, _Page)
        components = paginator.make_components(0).rows

        if await _check_embed_links(ctx, me):
            await ctx.respond(**page.to_kwargs(), components=components)

        else:
            await ctx.respond(page.to_content(locale=locale, localiser=localiser), components=components)


async def _check_embed_links(ctx: tanjun.abc.Context, me: hikari.OwnUser, /) -> bool:
    if ctx.guild_id is None:
        # The bot will always be able to embed links in DMs
        perms = hikari.Permissions.all_permissions()

    elif isinstance(ctx, tanjun.abc.AppCommandContext):
        assert ctx.interaction.app_permissions is not None
        perms = ctx.interaction.app_permissions

    else:
        # TODO: better handle caching member
        member = ctx.cache.get_member(ctx.guild_id, me) if ctx.cache else None
        member = member or await ctx.rest.fetch_member(ctx.guild_id, me)
        # TODO: this could handle caching the channel and roles better as well
        perms = await tanjun.permissions.fetch_permissions(ctx.client, member, channel=ctx.channel_id)

    return (perms & hikari.Permissions.EMBED_LINKS) == hikari.Permissions.EMBED_LINKS


@tanjun.as_loader
def load_help(client: tanjun.abc.Client) -> None:
    """Load this module's components into a bot."""
    help_config = client.injector.get_type_dependency(config.HelpConfig, default=_DEFAULT_CONFIG)

    component = tanjun.Component(name=_IDENTIFIER, strict=True)

    if help_config.enable_message_command:
        command = tanjun.MessageCommand(_help_command, "help")
        doc_parse.with_annotated_args(command)
        component.add_message_command(command)

    if help_config.enable_slash_command:
        command = doc_parse.as_slash_command(name="help")(_help_command)
        doc_parse.with_annotated_args(command)
        component.add_slash_command(command)

    client.add_component(component)

    client.add_client_callback(tanjun.ClientCallbackNames.COMPONENT_ADDED, reload)
    client.add_client_callback(tanjun.ClientCallbackNames.COMPONENT_REMOVED, reload)

    component_client = _internal.get_or_set_dep(client.injector, yuyo.ComponentClient, yuyo.ComponentClient)
    modal_client = _internal.get_or_set_dep(client.injector, yuyo.ModalClient, yuyo.ModalClient)

    try:
        static_index = client.get_type_dependency(yuyo.StaticPaginatorIndex)

    except KeyError:
        static_index = yuyo.StaticPaginatorIndex().add_to_clients(component_client, modal_client)

    reload(client=client, static_index=static_index, help_config=help_config)


# TODO: better document help.py and eval.py


@tanjun.as_unloader
def unload_help(client: tanjun.abc.Client) -> None:
    """Unload this module's components from a bot."""
    client.remove_component_by_name(_IDENTIFIER)
    client.remove_type_dependency(CommandDescriptions)
    client.remove_client_callback(tanjun.ClientCallbackNames.COMPONENT_ADDED, on_component_change)
    client.remove_client_callback(tanjun.ClientCallbackNames.COMPONENT_REMOVED, on_component_change)
    client.get_type_dependency(yuyo.StaticPaginatorIndex).remove_paginator(_IDENTIFIER)


# TODO: put the help command into a general/unnamed category
