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
"""Bot owner-only commands for dynamically executing code in the bot."""
from __future__ import annotations

__all__: list[str] = ["load_sudo", "unload_sudo"]

import ast
import asyncio
import contextlib
import copy
import inspect
import io
import itertools
import json
import random
import re
import time
import traceback
import typing
import urllib.parse
from typing import Annotated

import alluka
import hikari
import tanjun
import yuyo
from tanjun.annotations import Bool
from tanjun.annotations import Flag

from .. import _internal
from .. import doc_parse
from . import buttons
from . import config
from . import help as help_commands

if typing.TYPE_CHECKING:
    from collections import abc as collections

_COMPONENT_NAME = "tanchan.sudo"
"""Name of this module's component."""

_DEFAULT_CONFIG = config.EvalConfig()

_FAILED_COLOUR: typing.Final[hikari.Colour] = hikari.Colour(0xF04747)
"""Colour used to represent a failed execution/attempt."""

_FILE_EMOJI: typing.Final[hikari.UnicodeEmoji] = hikari.UnicodeEmoji("\N{CARD FILE BOX}\N{VARIATION SELECTOR-16}")
"""Emoji used for "to file" buttons."""

_PASS_COLOUR: typing.Final[hikari.Colour] = hikari.Colour(0x43B581)
"""Colour used to represent a successful execution/attempt."""

_PRIVATE_KEY = "p"
"""Query field name used to mark slash eval command responses as private."""

_THUMBS_UP_EMOJI = "\N{THUMBS UP SIGN}"
"""Emoji used to represent `True`."""

_THUMBS_DOWN_EMOJI = "\N{THUMBS DOWN SIGN}"
"""Emoji used to represent `False`."""

_CODEBLOCK_REGEX = re.compile(r"```(?:[\w]*\n?)([\s\S(^\\`{3})]*?)\n*```")
"""Regex used to extract code from a codeblock."""

_STATE_FILE_NAME = "EVAL_STATE"
"""Name of the file attachment used to store the eval call's code."""

_EDIT_BUTTON_EMOJI = "\N{SQUARED NEW}"
"""Emoji that's used for the edit button."""

_EVAL_MODAL_ID = "TC_EVAL"
"""Custom ID used for eval modals (including reruns)."""


def _yields_results(*args: io.StringIO) -> collections.Iterator[str]:
    """Create an iterator of the lines of an eval call's output."""
    for name, stream in zip(("stdout", "stderr"), args):
        yield f"- /dev/{name}:"
        while lines := stream.readlines(25):
            yield from (line[:-1] for line in lines)


async def _eval_python_code(
    client: tanjun.abc.Client,
    ctx: typing.Union[tanjun.abc.Context, yuyo.ComponentContext, yuyo.ModalContext],
    code: str,
    /,
    *,
    component: typing.Optional[tanjun.abc.Component] = None,
) -> tuple[io.StringIO, io.StringIO, int, bool]:
    """Evaluate python code while capturing the output."""
    stdout = io.StringIO()
    stderr = io.StringIO()

    stack = contextlib.ExitStack()
    stack.enter_context(contextlib.redirect_stdout(stdout))
    stack.enter_context(contextlib.redirect_stderr(stderr))

    start_time = time.perf_counter()
    try:
        with stack:
            await _eval_python_code_no_capture(client, ctx, code, component=component)

        failed = False
    except Exception:
        traceback.print_exc(file=stderr)
        failed = True
    finally:
        exec_time = round((time.perf_counter() - start_time) * 1000)

    stdout.seek(0)
    stderr.seek(0)
    return stdout, stderr, exec_time, failed


async def _eval_python_code_no_capture(
    client: tanjun.abc.Client,
    ctx: typing.Union[tanjun.abc.Context, yuyo.ComponentContext, yuyo.ModalContext],
    code: str,
    /,
    *,
    component: typing.Optional[tanjun.abc.Component] = None,
    file_name: str = "<string>",
) -> None:
    """Evaluate python code without capturing the output."""
    globals_ = {
        "app": ctx.shards,
        "asyncio": asyncio,
        "bot": ctx.shards,
        "client": client,
        "component": component,
        "ctx": ctx,
        "hikari": hikari,
        "tanjun": tanjun,
    }
    compiled_code = compile(code, file_name, "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
    if compiled_code.co_flags & inspect.CO_COROUTINE:
        await eval(compiled_code, globals_)  # noqa: S307 - insecure function

    else:
        eval(compiled_code, globals_)  # noqa: S307 - insecure function


def _bytes_from_io(
    stream: io.StringIO, name: str, mimetype: typing.Optional[str] = "text/x-python;charset=utf-8"
) -> hikari.Bytes:
    """Build Hikari bytes from an StringIO object."""
    stream.seek(0)
    return hikari.Bytes(stream, name, mimetype=mimetype)


async def _check_owner(
    client: tanjun.abc.Client,
    authors: tanjun.dependencies.AbstractOwners,
    # TODO: BaseContext needs stuff like the user attribute.
    ctx: typing.Union[yuyo.ComponentContext, yuyo.ModalContext],
) -> None:
    """Assert that the user who used a component or modal is the bot's owner."""
    if not await authors.check_ownership(client, ctx.interaction.user):
        raise yuyo.InteractionError("You cannot use this button")


@yuyo.modals.as_modal(ephemeral_default=True, parse_signature=True)
async def _eval_modal(
    ctx: yuyo.ModalContext,
    client: alluka.Injected[tanjun.abc.Client],
    component_client: alluka.Injected[yuyo.ComponentClient],
    authors: alluka.Injected[tanjun.dependencies.AbstractOwners],
    *,
    content: str = yuyo.modals.text_input("Content", style=hikari.TextInputStyle.PARAGRAPH),
    raw_file_output: str = yuyo.modals.text_input(
        "File output (y/n)", default=_THUMBS_DOWN_EMOJI, min_length=1, max_length=5
    ),
) -> None:
    """Evaluate the input from an eval modal call."""
    try:
        file_output = tanjun.conversion.to_bool(raw_file_output)

    except ValueError:
        raise yuyo.InteractionError("Invalid value passed for File output") from None

    await _check_owner(client, authors, ctx)
    if ctx.interaction.message:
        # Being executed as a button attached to an eval call's response to edit it.
        # TODO: we shouldn't actually need to pass ephemeral=False when doing a message update response
        await ctx.create_initial_response(ephemeral=False, response_type=hikari.ResponseType.MESSAGE_UPDATE)

    else:
        # Being executed in response to the slash command.
        query = urllib.parse.parse_qs(ctx.id_metadata).get(_PRIVATE_KEY)
        ephemeral = tanjun.conversion.to_bool(query[0]) if query else False
        await ctx.create_initial_response("Loading...", ephemeral=ephemeral)

    state = json.dumps({"content": content, "file_output": file_output})
    await _eval_message_command(
        ctx,
        client,
        component_client,
        content=content,
        file_output=file_output,
        state_attachment=hikari.Bytes(state, _STATE_FILE_NAME),
    )


def _make_rows(
    *, default: typing.Optional[str] = None, file_output: typing.Optional[bool] = None
) -> collections.Sequence[hikari.api.ModalActionRowBuilder]:
    """Make a custom instance of the eval modal's rows with the eval content pre-set."""
    rows = list(_eval_modal.rows)
    content_row = _eval_modal.rows[0]
    if default is not None:
        assert isinstance(content_row.components[0], hikari.api.TextInputBuilder)
        rows[0] = hikari.impl.ModalActionRowBuilder().add_component(
            copy.copy(content_row.components[0]).set_value(default)
        )

    button_row = _eval_modal.rows[1]
    if file_output is not None:
        assert isinstance(button_row.components[0], hikari.api.TextInputBuilder)
        file_output_repr = _THUMBS_UP_EMOJI if file_output else _THUMBS_DOWN_EMOJI
        rows[1] = hikari.impl.ModalActionRowBuilder().add_component(
            copy.copy(button_row.components[0]).set_value(file_output_repr)
        )

    return rows


@yuyo.components.as_single_executor(_EVAL_MODAL_ID, ephemeral_default=True)
async def _on_edit_button(
    ctx: yuyo.ComponentContext,
    client: alluka.Injected[tanjun.abc.Client],
    authors: alluka.Injected[tanjun.dependencies.AbstractOwners],
) -> None:
    """Handle calls to the eval edit button."""
    await _check_owner(client, authors, ctx)
    rows = _eval_modal.rows
    # Try to get the old eval call's code
    for attachment in ctx.interaction.message.attachments:
        # If the edit button has been used already then a state file will be present.
        if attachment.filename != _STATE_FILE_NAME:
            continue

        try:
            data = await attachment.read()

        except hikari.HikariError:
            break

        try:
            data = json.loads(data)

        # Backwards compatibility with old eval responses which just stored
        # the eval code in the file output file raw without any json wrapping.
        except json.JSONDecodeError:
            rows = _make_rows(default=data.decode())

        else:
            rows = _make_rows(default=data["content"], file_output=data["file_output"])

        break

    else:
        # Otherwise try to get the source message.
        message = await client.rest.fetch_message(ctx.interaction.channel_id, ctx.interaction.message)
        if message.referenced_message and message.referenced_message.content:
            parsed = _CODEBLOCK_REGEX.findall(message.referenced_message.content)
            try:
                default = parsed[0]

            except IndexError:
                pass

            else:
                rows = _make_rows(default=default)

    await ctx.create_modal_response("Edit eval", _EVAL_MODAL_ID, components=rows)


async def _never(ctx: yuyo.ComponentContext) -> None:
    raise RuntimeError("Shouldn't be reached")


class _FileCallback:
    """Callback logic used for to file buttons."""

    __slots__ = ("_custom_id", "_files", "_make_files", "_post_components", "__weakref__")

    def __init__(
        self,
        custom_id: str,
        /,
        *,
        files: collections.Sequence[hikari.Resourceish] = (),
        make_files: typing.Optional[collections.Callable[[], collections.Sequence[hikari.Resourceish]]] = None,
        post_components: typing.Optional[yuyo.ActionColumnExecutor] = None,
    ) -> None:
        """Initialise a file callback.

        .. note::
            `files` and `make_files` are mutually exclusive.

        Parameters
        ----------
        custom_id
            The button's custom ID.
        files
            Collection of the files to send when the to file button is pressed.
        make_files
            A callback which returns the files tosend when the to file button is
            pressed.
        post_components
            Components to include on the updated message.
        """
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
        await ctx.respond(attachments=files, component=buttons.delete_row(ctx.interaction.user.id))


def _add_file_button(
    column: yuyo.components.ActionColumnExecutor,
    /,
    *,
    files: collections.Sequence[hikari.Resourceish] = (),
    make_files: typing.Optional[collections.Callable[[], collections.Sequence[hikari.Resourceish]]] = None,
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
    custom_id = random.randbytes(32).hex()  # noqa: S311
    column.add_interactive_button(
        hikari.ButtonStyle.SECONDARY,
        _FileCallback(custom_id, files=files, make_files=make_files, post_components=column),
        custom_id=custom_id,
        emoji=_FILE_EMOJI,
    )


@help_commands.hide_from_help
@tanjun.annotations.with_annotated_args
@tanjun.as_message_command("eval", "exec")
async def _eval_message_command(
    ctx: typing.Union[tanjun.abc.MessageContext, yuyo.ModalContext],
    client: alluka.Injected[tanjun.abc.Client],
    component_client: alluka.Injected[yuyo.ComponentClient],
    *,
    content: typing.Optional[str] = None,
    component: alluka.Injected[typing.Optional[tanjun.abc.Component]] = None,
    file_output: Annotated[Bool, Flag(empty_value=True, aliases=["-f", "--file-out", "--file"])] = False,
    state_attachment: typing.Optional[hikari.Bytes] = None,
    suppress_response: Annotated[Bool, Flag(empty_value=True, aliases=["-s", "--suppress"])] = False,
) -> None:
    """Owner only command used to dynamically evaluate a script."""
    if isinstance(ctx, tanjun.abc.MessageContext):
        code = _CODEBLOCK_REGEX.findall(ctx.content)
        kwargs: dict[str, typing.Any] = {"reply": ctx.message.id}
        respond = ctx.respond

        if not code:
            raise tanjun.CommandError("Expected a python code block.", component=buttons.delete_row(ctx.author.id))

        code = code[0]

    else:
        assert content is not None
        code = content
        kwargs = {}
        respond = ctx.edit_initial_response

    if suppress_response:
        # Doesn't want a response, just run the eval to completion
        await _eval_python_code_no_capture(client, ctx, code, component=component)
        return

    stdout, stderr, exec_time, failed = await _eval_python_code(client, ctx, code, component=component)
    attachments = [state_attachment] if state_attachment else []

    if file_output:
        # Wants the output to be attached as two files, avoid building a paginator.
        message = await respond(
            "",
            attachments=[
                hikari.Bytes(stdout, "stdout.py", mimetype="text/x-python;charset=utf-8"),
                hikari.Bytes(stderr, "stderr.py", mimetype="text/x-python;charset=utf-8"),
                *attachments,
            ],
            component=buttons.delete_row(ctx.author.id).add_interactive_button(
                hikari.ButtonStyle.SECONDARY, _EVAL_MODAL_ID, emoji=_EDIT_BUTTON_EMOJI
            ),
            embeds=[],
            **kwargs,
        )
        _try_deregister(component_client, message)
        return

    colour = _FAILED_COLOUR if failed else _PASS_COLOUR
    string_paginator = yuyo.sync_paginate_string(
        _yields_results(stdout, stderr), wrapper="```python\n{}\n```", char_limit=2034
    )
    embed_generator = (
        hikari.Embed(colour=colour, description=text, title=f"Eval page {page + 1}").set_footer(
            text=f"Time taken: {exec_time} ms"
        )
        for page, text in enumerate(string_paginator)
    )
    paginator = (
        yuyo.ComponentPaginator(map(yuyo.Page, embed_generator), authors=[ctx.author.id], triggers=[])
        .add_first_button()
        .add_previous_button()
        .add_stop_button(custom_id=buttons.make_delete_id(ctx.author.id))
        .add_next_button()
        .add_last_button()
    )

    first_response = await paginator.get_next_entry()
    _add_file_button(
        paginator, make_files=lambda: [_bytes_from_io(stdout, "stdout.py"), _bytes_from_io(stderr, "stderr.py")]
    )
    paginator.add_interactive_button(
        hikari.ButtonStyle.SECONDARY, _never, custom_id=_EVAL_MODAL_ID, emoji=_EDIT_BUTTON_EMOJI
    )

    assert first_response is not None
    message = await respond(
        **first_response.to_kwargs() | {"attachments": attachments, "content": ""}, components=paginator.rows, **kwargs
    )
    _try_deregister(component_client, message)
    component_client.register_executor(paginator, message=message)


def _try_deregister(client: yuyo.ComponentClient, message: hikari.Message) -> None:
    with contextlib.suppress(KeyError):
        client.deregister_message(message)


async def _eval_slash_command(
    ctx: tanjun.abc.SlashContext, file_output: typing.Optional[Bool] = None, private: Bool = False
) -> None:
    """Owner only command used to dynamically evaluate a script.

    This can only be used by the bot's owner.

    Parameters
    ----------
    file_output
        Whether this should send the output as embeddable txt files.

        Defaults to False.
    private
        Whether the output should be sent as a private message. Defaults to false.
    """
    custom_id = f"{_EVAL_MODAL_ID}:{_PRIVATE_KEY}={int(private)}"
    await ctx.create_modal_response("Eval", custom_id, components=_make_rows(file_output=file_output))


class _OnGuildCreate:
    """Handles creating the eval slash command for the whitelisted guilds on guild create."""

    __slots__ = ("_command", "__weakref__")

    # TODO: tanjun just needs type var defaults at this point
    def __init__(self, command: tanjun.abc.SlashCommand[typing.Any], /) -> None:
        self._command = command

    async def __call__(
        self,
        event: typing.Union[hikari.GuildJoinEvent, hikari.GuildAvailableEvent],
        eval_config: alluka.Injected[config.EvalConfig] = _DEFAULT_CONFIG,
    ) -> None:
        """Guild create listener which declares the eval slash command."""
        # TODO: come up with a better system for overriding command.is_global
        # TODO: deregister slash command if it shouldn't be present
        if eval_config.eval_guild_ids is not None and event.guild_id in eval_config.eval_guild_ids:
            app = await event.app.rest.fetch_application()
            await self._command.build().create(event.app.rest, app.id, guild=event.guild_id)


@tanjun.as_loader
def load_sudo(client: tanjun.abc.Client) -> None:
    """Load this module's components into a bot."""
    eval_config = client.injector.get_type_dependency(config.EvalConfig, default=_DEFAULT_CONFIG)
    component = (
        tanjun.Component(name=_COMPONENT_NAME, strict=True)
        .add_message_command(_eval_message_command)
        .add_check(tanjun.checks.OwnerCheck())
    )

    if eval_config.eval_guild_ids or eval_config.eval_guild_ids is None:
        # TODO: with_annotated and as_slash_command just need public non-decorator equivalents
        is_global = eval_config.eval_guild_ids is None
        eval_command = doc_parse.as_slash_command(name="eval", is_global=is_global)(_eval_slash_command)
        help_commands.hide_from_help(eval_command)
        doc_parse.with_annotated_args(eval_command)
        component.add_command(eval_command)

        if not is_global:
            on_guild_create = _OnGuildCreate(eval_command)
            component.add_listener(hikari.GuildJoinEvent, on_guild_create).add_listener(
                hikari.GuildAvailableEvent, on_guild_create
            )

    client.add_component(component)

    _internal.get_or_set_dep(client.injector, yuyo.ComponentClient, yuyo.ComponentClient).register_executor(
        _on_edit_button, timeout=None
    )
    _internal.get_or_set_dep(client.injector, yuyo.ModalClient, yuyo.ModalClient).register_modal(
        _EVAL_MODAL_ID, _eval_modal, timeout=None
    )


@tanjun.as_unloader
def unload_sudo(client: tanjun.abc.Client) -> None:
    """Unload this module's components from a bot."""
    client.remove_component_by_name(_COMPONENT_NAME)

    component_client = client.injector.get_type_dependency(yuyo.ComponentClient)
    modal_client = client.injector.get_type_dependency(yuyo.ModalClient)
    assert component_client
    assert modal_client
    component_client.deregister_executor(_on_edit_button)
    modal_client.deregister_modal(_EVAL_MODAL_ID)
