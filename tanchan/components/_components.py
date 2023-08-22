# -*- coding: utf-8 -*-
# BSD 3-Clause License
#
# Copyright (c) 2020-2023, Faster Speeding
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
from __future__ import annotations

__all__: list[str] = []

import itertools
import random
import typing

import hikari
import yuyo

if typing.TYPE_CHECKING:
    from collections import abc as collections

DELETE_CUSTOM_ID = "AUTHOR_DELETE_BUTTON"
"""Prefix ID used for delete buttons."""

DELETE_EMOJI: typing.Final[hikari.UnicodeEmoji] = hikari.UnicodeEmoji(
    "\N{HEAVY MULTIPLICATION X}\N{VARIATION SELECTOR-16}"
)
"""Emoji used for "delete" buttons."""

FILE_EMOJI: typing.Final[hikari.UnicodeEmoji] = hikari.UnicodeEmoji("\N{CARD FILE BOX}\N{VARIATION SELECTOR-16}")
"""Emoji used for "to file" buttons."""


def make_delete_id(*authors: hikari.SnowflakeishOr[hikari.User]) -> str:
    """Make a delete button custom ID."""
    return DELETE_CUSTOM_ID + ":authors=" + ",".join(str(int(author)) for author in authors)


def delete_row_from_authors(*authors: hikari.Snowflakeish) -> hikari.impl.MessageActionRowBuilder:
    """Make an action row builder with a delete button from a list of authors.

    Parameters
    ----------
    *authors
        IDs of authors who should be allowed to delete the response.

        Both user IDs and role IDs are supported with no IDs indicating
        that anybody should be able to delete the response.

    Returns
    -------
    hikari.impl.ActionRowBuilder
        Action row builder with a delete button.
    """
    return hikari.impl.MessageActionRowBuilder().add_interactive_button(
        hikari.ButtonStyle.DANGER, make_delete_id(*authors), emoji=DELETE_EMOJI
    )


class FileCallback:
    """Callback logic used for to file buttons.

    .. note::
        `files` and `make_files` are mutually exclusive.

    Parameters
    ----------
    ctx
        The command context this is linked to.
    files
        Collection of the files to send when the to file button is pressed.
    make_files
        A callback which returns the files tosend when the to file button is
        pressed.
    """

    __slots__ = ("_custom_id", "_files", "_make_files", "_post_components", "__weakref__")

    def __init__(
        self,
        custom_id: str,
        /,
        *,
        files: collections.Sequence[hikari.Resourceish] = (),
        make_files: collections.Callable[[], collections.Sequence[hikari.Resourceish]] | None = None,
        post_components: yuyo.ActionColumnExecutor | None = None,
    ) -> None:
        self._custom_id = custom_id
        self._files = files
        self._make_files = make_files
        self._post_components = post_components

    async def __call__(self, ctx: yuyo.ComponentContext) -> None:
        if self._post_components:
            rows = self._post_components.rows
            for component in itertools.chain.from_iterable(row.components for row in rows):
                if (
                    isinstance(component, hikari.api.InteractiveButtonBuilder)
                    and component.custom_id == self._custom_id
                ):
                    component.set_is_disabled(True)

            await ctx.create_initial_response(components=rows, response_type=hikari.ResponseType.MESSAGE_UPDATE)

        files = self._make_files() if self._make_files else self._files
        await ctx.respond(attachments=files, component=delete_row_from_authors(ctx.interaction.user.id))


def add_file_button(
    column: yuyo.components.ActionColumnExecutor,
    /,
    *,
    files: collections.Sequence[hikari.Resourceish] = (),
    make_files: collections.Callable[[], collections.Sequence[hikari.Resourceish]] | None = None,
) -> None:
    """Add a file button to a component column.

    .. note::
        `files` and `make_files` are mutually exclusive.

    Parameters
    ----------
    column
        The column to add the button to.
    files
        Collection of the files to send when the to file button is pressed.
    make_files
        A callback which returns the files to send when the to file button is
        pressed.
    """
    custom_id = random.randbytes(32).hex()
    column.add_interactive_button(
        hikari.ButtonStyle.SECONDARY,
        FileCallback(custom_id, files=files, make_files=make_files, post_components=column),
        custom_id=custom_id,
        emoji=FILE_EMOJI,
    )
