# -*- coding: utf-8 -*-
# BSD 3-Clause License
#
# Copyright (c) 2023, Faster Speeding
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
"""A components powered help command."""  # TODO: note that these are speciically for message commands
from __future__ import annotations

__all__: list[str] = ["load_help", "unload_help"]

import hashlib
import inspect
import itertools
import typing
import urllib.parse
from typing import Annotated

import alluka
import hikari
import tanjun
import yuyo
from tanjun.annotations import Positional
from tanjun.annotations import Str

from .. import _internal
from .. import doc_parse
from . import _components

if typing.TYPE_CHECKING:
    from collections import abc as collections

_CommandT = typing.TypeVar("_CommandT", bound=tanjun.abc.ExecutableCommand[typing.Any])


_AUTHOR_KEY = "a"
_CATEGORY_KEY = "TANCHAN_HELP_CATEGORY"
_DESCRIPTION_KEY = "TANCHAN_HELP_DESCRIPTIOn"
_HASH_KEY = "h"
_PAGE_NUM_KEY = "p"
_NUMBERS_MODAL_ID = "tanchan.help.to_page"


def with_help(
    description: typing.Optional[str] = None, /, *, category: typing.Optional[str] = None, follow_wrapped: bool = False
) -> collections.Callable[[_CommandT], _CommandT]:
    """Override the help string for the command.

    Examples
    --------
    description
    follow_wrapped
    """

    def decorator(cmd: _CommandT, /) -> _CommandT:
        if description is not None:
            cmd.metadata[_DESCRIPTION_KEY] = description

        if category is not None:
            cmd.metadata[_CATEGORY_KEY] = category

        _internal.apply_to_wrapped(cmd, decorator, follow_wrapped=follow_wrapped)
        return cmd

    return decorator


def hide_from_help(
    cmd: typing.Optional[_CommandT] = None, /, *, follow_wrapped: bool = False
) -> typing.Union[_CommandT, collections.Callable[[_CommandT], _CommandT]]:
    """Hide a global command from the help command.

    Parameters
    ----------
    follow_wrapped

    Examples
    --------
    ```py
    @hide_from_command
    ```
    """

    def decorator(cmd: _CommandT, /) -> _CommandT:
        cmd.metadata[_DESCRIPTION_KEY] = None
        _internal.apply_to_wrapped(cmd, hide_from_help, follow_wrapped=follow_wrapped)
        return cmd

    if cmd:
        return decorator(cmd)

    return decorator


def _filter_name(name: str, /) -> list[str]:
    return name.casefold().split()


class _HelpIndex:
    __slots__ = ("_column", "_descriptions", "_hash", "_numbers", "_pages")

    def __init__(self) -> None:
        self._descriptions: dict[tuple[str, ...], typing.Optional[str]] = {}
        self._hash = ""
        self._pages: list[str] = []
        self._column = _HelpColumn(self)
        self._numbers = _NumberModal(self)

    @property
    def column(self) -> _HelpColumn:
        return self._column

    @property
    def hash(self) -> str:
        return self._hash

    @property
    def numbers_modal(self) -> _NumberModal:
        return self._numbers

    @property
    def pages(self) -> collections.Sequence[str]:
        return self._pages

    def form_page(
        self, permissions: typing.Optional[hikari.Permissions], index: int, /
    ) -> typing.Optional[yuyo.pagination.Page]:
        try:
            page = self._pages[index - 1]

        except IndexError:
            return None

        # perms is None indicates a DM where we will always have embed links.
        if permissions is None or permissions & hikari.Permissions.EMBED_LINKS:
            return yuyo.pagination.Page(
                embed=hikari.Embed(title="Command descriptions", description=page).set_footer(
                    f"Help page {index}/{len(self._pages)}"
                )
            )

        else:
            return yuyo.pagination.Page(f"```md\n{page}\n```")

    async def on_refresh(self, _: tanjun.abc.Component, client: alluka.Injected[tanjun.abc.Client]) -> None:
        for command in client.iter_message_commands():
            component_name = command.component.name if command.component else "unknown"
            categories: dict[str, list[tanjun.abc.ExecutableCommand[typing.Any]]] = {}
            names: typing.Optional[list[tuple[str, ...]]] = None
            other_commands = command.commands if isinstance(command, tanjun.abc.MessageCommandGroup) else ()

            for command in itertools.chain((command,), other_commands):
                if not names:
                    names = [tuple(_filter_name(n)) for n in command.names]

                else:
                    names = [(*p, *_filter_name(n)) for p, n in itertools.product(names, command.names)]

                if description_override := command.metadata.get(_DESCRIPTION_KEY):
                    if not isinstance(description_override, str):
                        description_override = None

                else:
                    continue

                description = description_override or inspect.getdoc(command.callback)
                # TODO: handle inheriting this state from parent commands
                category = command.metadata.get(_CATEGORY_KEY) or component_name
                try:
                    categories[category].append(command)

                except KeyError:
                    categories[category] = [command]

                for name in names:
                    self._descriptions[name] = description

        items_repr = ((" ".join(k), v or "") for k, v in self._descriptions.items())
        items_repr = ",".join(map(":".join, sorted(items_repr, key=lambda v: v[0]))).encode()
        self._hash = "md5-" + hashlib.md5(items_repr, usedforsecurity=False).hexdigest()

    def find_command(self, command_name: str, /) -> typing.Optional[str]:
        self._descriptions.get(tuple(_filter_name(command_name)))


class _NumberModal(yuyo.modals.Modal):
    __slots__ = ("_index",)

    def __init__(self, index: _HelpIndex, /) -> None:
        super().__init__(ephemeral_default=True)
        self._index = index

    async def callback(
        self, ctx: yuyo.ModalContext, field: str = yuyo.modals.text_input("Page number", min_length=1)
    ) -> None:
        try:
            page_number = int(field)
        except ValueError:
            raise yuyo.InteractionError(
                "Not a valid number", component=_components.delete_row_from_authors(ctx.author.id)
            ) from None

        # TODO: what is ctx.interaction.app_permissions when the app itself isn't present?
        if page := self._index.form_page(ctx.interaction.app_permissions, page_number):
            await ctx.create_initial_response(
                **page.to_kwargs(),
                components=self._index.column.rows,
                ephemeral=False,
                response_type=hikari.ResponseType.MESSAGE_UPDATE,
            )

        else:
            await ctx.respond("Page not found")


async def _noop(ctx: yuyo.ComponentContext, /) -> None:
    await ctx.create_initial_response(response_type=hikari.ResponseType.MESSAGE_UPDATE)


class _HelpColumn(yuyo.ActionColumnExecutor):
    __slots__ = ("_index",)

    def __init__(
        self, index: _HelpIndex, /, *, author: typing.Optional[hikari.Snowflake] = None, page: int = 0
    ) -> None:
        metadata = f"{_HASH_KEY}={index.hash}&{_PAGE_NUM_KEY}={page}"
        if author:
            metadata += f"&{_AUTHOR_KEY}={int(author)}"

        super().__init__(
            ephemeral_default=True,
            id_metadata={
                "jump_to_start": metadata,
                "previous_button": metadata,
                "stop_button": str(int(author)) if author else "",
                "next_button": metadata,
                "jump_to_last": metadata,
                "numbers_button": metadata,
            },
        )
        self._index = index

    def _make_rows(
        self, author: hikari.Snowflake, page: int, /
    ) -> collections.Sequence[hikari.api.MessageActionRowBuilder]:
        return _HelpColumn(self._index, author=author, page=page).rows

    def _process_metadata(self, ctx: yuyo.ComponentContext, /) -> int:
        metadata = urllib.parse.parse_qs(ctx.id_metadata)

        if int(metadata[_AUTHOR_KEY][0]) != ctx.author.id:
            raise yuyo.InteractionError(
                "You cannot use this button", component=_components.delete_row_from_authors(ctx.author.id)
            )

        if metadata[_HASH_KEY][0] != self._index.hash:
            raise yuyo.InteractionError(
                "This help command instance is out of date",
                component=_components.delete_row_from_authors(ctx.author.id),
            )

        return int(metadata[_PAGE_NUM_KEY][0])

    async def to_page(self, ctx: yuyo.ComponentContext, index: int, /) -> None:
        if page := self._index.form_page(ctx.interaction.app_permissions, index):
            rows = self._make_rows(ctx.author.id, index)
            await ctx.create_initial_response(
                page.to_kwargs(), components=rows, response_type=hikari.ResponseType.MESSAGE_UPDATE
            )

        else:
            raise yuyo.InteractionError("Page not found", component=_components.delete_row_from_authors(ctx.author.id))

    @yuyo.components.as_interactive_button(hikari.ButtonStyle.SECONDARY, emoji=yuyo.pagination.LEFT_DOUBLE_TRIANGLE)
    async def jump_to_start(self, ctx: yuyo.ComponentContext) -> None:
        self._process_metadata(ctx)
        await self.to_page(ctx, 1)

    @yuyo.components.as_interactive_button(hikari.ButtonStyle.SECONDARY, emoji=yuyo.pagination.LEFT_TRIANGLE)
    async def previous_button(self, ctx: yuyo.ComponentContext) -> None:
        page_number = self._process_metadata(ctx)
        if page_number <= 0:
            await _noop(ctx)

        else:
            await self.to_page(ctx, page_number - 1)

    @yuyo.components.as_interactive_button(
        hikari.ButtonStyle.DANGER, custom_id=_components.DELETE_CUSTOM_ID, emoji=yuyo.pagination.BLACK_CROSS
    )
    async def stop_button(self, ctx: yuyo.ComponentContext) -> None:
        ...

    @yuyo.components.as_interactive_button(hikari.ButtonStyle.SECONDARY, emoji=yuyo.pagination.RIGHT_TRIANGLE)
    async def next_button(self, ctx: yuyo.ComponentContext) -> None:
        page_number = self._process_metadata(ctx)
        if page_number >= len(self._index.pages):
            await _noop(ctx)

        else:
            await self.to_page(ctx, page_number + 1)

    @yuyo.components.as_interactive_button(hikari.ButtonStyle.SECONDARY, emoji=yuyo.pagination.RIGHT_DOUBLE_TRIANGLE)
    async def jump_to_last(self, ctx: yuyo.ComponentContext) -> None:
        self._process_metadata(ctx)
        await self.to_page(ctx, len(self._index.pages))

    @yuyo.components.as_interactive_button(hikari.ButtonStyle.SECONDARY, emoji="\N{INPUT SYMBOL FOR NUMBERS}")
    async def numbers_button(self, ctx: yuyo.ComponentContext) -> None:
        self._process_metadata(ctx)
        await ctx.create_modal_response("Select page", _NUMBERS_MODAL_ID, components=self._index.numbers_modal.rows)


@doc_parse.with_annotated_args(follow_wrapped=True)
@tanjun.as_message_command("help")
@doc_parse.as_slash_command(name="help")
async def help_command(
    ctx: tanjun.abc.Context,
    *,
    command_name: Annotated[Str | None, Positional()] = None,
    index: alluka.Injected[_HelpIndex],
    # TODO: switch cached_inject over to using an injected cache to avoid
    # edge case state issues
    # This could likely also include adding a "ScopedState" return class
    # which lets you scope them per specific resource (e.g. user, member)
    me: hikari.OwnUser = tanjun.cached_inject(tanjun.dependencies.fetch_my_user),
) -> None:
    """Get information about the bot's commands.

    Parameters
    ----------
    command_name
        Name of a command to get the full information for.
    """
    if command_name:
        content = index.find_command(command_name)
        components: collections.Sequence[hikari.api.MessageActionRowBuilder] = []

        if not content:
            raise tanjun.CommandError(
                "Couldn't find command", component=_components.delete_row_from_authors(ctx.author.id)
            )

    else:
        # TODO: proper intro page + page numbers
        content = index.pages[0]
        components = _HelpColumn(index, author=ctx.author.id).rows

    if ctx.guild_id is None:
        # The bot will always be able to embed links in DMs
        perms = hikari.Permissions.EMBED_LINKS

    elif isinstance(ctx, tanjun.abc.AppCommandContext):
        assert ctx.interaction.app_permissions is not None
        perms = ctx.interaction.app_permissions

    else:
        # TODO: better handle caching member
        member = ctx.cache.get_member(ctx.guild_id, me) if ctx.cache else None
        member = member or await ctx.rest.fetch_member(ctx.guild_id, me)
        # TODO: this could handle caching the channel and roles better as well
        perms = await tanjun.permissions.fetch_permissions(ctx.client, member, channel=ctx.channel_id)

    if perms & hikari.Permissions.EMBED_LINKS:
        await ctx.respond(embed=hikari.Embed(description=content), components=components)

    else:
        await ctx.respond(f"```md\n{content}\n```", components=components)


@tanjun.as_loader
def load_help(client: tanjun.abc.Client) -> None:
    """Load this module's components into a bot."""
    index = _HelpIndex()
    client.add_client_callback(tanjun.ClientCallbackNames.COMPONENT_ADDED, index.on_refresh)
    client.add_client_callback(tanjun.ClientCallbackNames.COMPONENT_REMOVED, index.on_refresh)
    client.injector.set_type_dependency(_HelpIndex, index)

    component_client = client.injector.get_type_dependency(yuyo.ComponentClient)
    modal_client = client.injector.get_type_dependency(yuyo.ModalClient)

    if not component_client:
        # TODO: or raise a missing dep error?
        component_client = yuyo.ComponentClient.from_tanjun(client)

    if not modal_client:
        # TODO: or raise a missing dep error?
        modal_client = yuyo.ModalClient.from_tanjun(client)

    component_client.register_executor(index.column, timeout=None)
    modal_client.register_modal(_NUMBERS_MODAL_ID, index.numbers_modal, timeout=None)


@tanjun.as_unloader
def unload_help(client: tanjun.abc.Client) -> None:
    """Unload this module's components from a bot."""
    index = client.get_type_dependency(_HelpIndex)
    component_client = client.injector.get_type_dependency(yuyo.ComponentClient)
    modal_client = client.injector.get_type_dependency(yuyo.ModalClient)
    assert index
    assert component_client
    assert modal_client

    client.remove_client_callback(tanjun.ClientCallbackNames.COMPONENT_ADDED, index.on_refresh)
    client.remove_client_callback(tanjun.ClientCallbackNames.COMPONENT_REMOVED, index.on_refresh)
    client.injector.remove_type_dependency(_HelpIndex)
    component_client.deregister_executor(index.column)
    modal_client.deregister_modal(_NUMBERS_MODAL_ID)


_component = tanjun.Component(name="tanchan.help", strict=True).load_from_scope()
