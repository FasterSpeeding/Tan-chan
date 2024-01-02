# -*- coding: utf-8 -*-
# BSD 3-Clause License
#
# Copyright (c) 2020-2024, Faster Speeding
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
"""Standard constant message components provided and used by Tanchan."""
from __future__ import annotations

__all__: list[str] = ["load_buttons", "unload_buttons"]

import itertools
import typing
import urllib.parse

import hikari
import tanjun
import yuyo

from .. import _internal

if typing.TYPE_CHECKING:
    from collections import abc as collections


DELETE_CUSTOM_ID: typing.Final[str] = "TC_DEL"
"""Match ID used for delete buttons."""

DELETE_EMOJI: typing.Final[hikari.UnicodeEmoji] = hikari.UnicodeEmoji(
    "\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}"
)
"""Emoji used for "delete" buttons."""

OWNER_QS_KEY: typing.Final[str] = "a"
"""Query string key for the author field."""


def make_delete_id(author: hikari.SnowflakeishOr[hikari.User], /, *authors: hikari.SnowflakeishOr[hikari.User]) -> str:
    """Make a delete button custom ID."""
    return f"{DELETE_CUSTOM_ID}:{OWNER_QS_KEY}={int(author)}," + ",".join(str(int(author)) for author in authors)


def delete_row(
    ctx_or_author: typing.Union[
        hikari.Snowflakeish, tanjun.abc.Context, tanjun.abc.AutocompleteContext, yuyo.components.BaseContext[typing.Any]
    ],
    /,
    *ctx_or_authors: typing.Union[
        hikari.Snowflakeish, tanjun.abc.Context, tanjun.abc.AutocompleteContext, yuyo.components.BaseContext[typing.Any]
    ],
) -> hikari.impl.MessageActionRowBuilder:
    """Make an action row builder with a delete button from a list of authors.

    Parameters
    ----------
    *ctx_or_authors
        IDs of authors who should be allowed to delete the response.

        Both user IDs and role IDs are supported with no IDs indicating
        that anybody should be able to delete the response.

        Tanjun and Yuyo contexts can also be passed here to target their
        author.

    Returns
    -------
    hikari.impl.ActionRowBuilder
        Action row builder with a delete button.
    """
    authors = (value if isinstance(value, int) else value.author.id for value in ctx_or_authors)
    custom_id = make_delete_id(ctx_or_author if isinstance(ctx_or_author, int) else ctx_or_author.author.id, *authors)
    return hikari.impl.MessageActionRowBuilder().add_interactive_button(
        hikari.ButtonStyle.DANGER, custom_id, emoji=DELETE_EMOJI
    )


@yuyo.components.as_single_executor(DELETE_CUSTOM_ID)
async def on_delete_button(ctx: yuyo.ComponentContext, /) -> None:
    """Default implementation of a constant callback used by delete buttons.

    Parameters
    ----------
    ctx
        The context that triggered this delete.
    """
    query = urllib.parse.parse_qs(ctx.id_metadata)
    # Indicates a query string is being used.
    if query:
        raw_ids = query.get(OWNER_QS_KEY)
        author_ids = set(itertools.chain.from_iterable(map(_parse_owner_ids, raw_ids))) if raw_ids else None

    # Old ID list only approach.
    else:
        author_ids = set(_parse_owner_ids(ctx.id_metadata))

    if (
        not author_ids  # no IDs == public
        or ctx.interaction.user.id in author_ids
        or ctx.interaction.member
        and author_ids.intersection(ctx.interaction.member.role_ids)
    ):
        await ctx.defer(defer_type=hikari.ResponseType.DEFERRED_MESSAGE_UPDATE)
        await ctx.delete_initial_response()

    else:
        await ctx.create_initial_response(
            "You do not own this message",
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            flags=hikari.MessageFlag.EPHEMERAL,
        )


# TODO: should be typed as returning an iterator of snowflakes.
def _parse_owner_ids(value: str, /) -> collections.Iterator[int]:
    # Filter is needed as "".split(",") will give [""] which is not a valid snowflake.
    # And "123," will give ["123", ""].
    return map(hikari.Snowflake, filter(None, value.split(",")))


@tanjun.as_loader
def load_buttons(client: tanjun.abc.Client) -> None:
    """Load this module's components into a bot."""
    component_client = _internal.get_or_set_dep(client.injector, yuyo.ComponentClient, yuyo.ComponentClient)
    try:
        component_client.register_executor(on_delete_button, timeout=None)

    except ValueError:
        pass  # They have their own implementation set.


@tanjun.as_unloader
def unload_buttons(client: tanjun.abc.Client) -> None:
    """Unload this module's components from a bot."""
    component_client = client.injector.get_type_dependency(yuyo.ComponentClient)
    assert component_client
    # TODO: only remove if get_executor_fur_id(DELETE_CUSTOM_ID) is on_delete_button
    component_client.deregister_executor(on_delete_button)
