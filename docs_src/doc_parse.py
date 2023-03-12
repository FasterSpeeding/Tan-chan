# -*- coding: utf-8 -*-
# Tanchan Examples - A collection of examples for Tanchan.
# Written in 2023 by Lucina Lucina@lmbyrne.dev
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain worldwide.
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this software.
# If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.
import sys
import time
import typing

import tanjun
from tanjun import annotations

from tanchan import doc_parse

assert sys.version_info >= (3, 11)


def as_slash_command_example():
    @doc_parse.as_slash_command()  # This command will be called "ping"
    async def ping(ctx: tanjun.abc.SlashContext) -> None:
        """Get the bot's latency."""
        start_time = time.perf_counter()
        await ctx.rest.fetch_my_user()
        time_taken = (time.perf_counter() - start_time) * 1_000
        await ctx.respond(f"PONG\n - REST: {time_taken:.0f}mss")


def with_annotated_args_example():
    @doc_parse.with_annotated_args
    @doc_parse.as_slash_command()
    async def toggle_setting(ctx: tanjun.abc.Context, user: annotations.User, state: annotations.Bool = False) -> None:
        """Toggle this setting for a user.

        Parameters
        ----------
        user
            The user to toggle this setting for.
        state
            Whether this should be enabled.
        """

    @doc_parse.with_annotated_args
    @doc_parse.as_slash_command()
    async def ban_user(ctx: tanjun.abc.Context, user: annotations.User) -> None:
        """Ban a user from this guild.

        Args:
            user:
                The user to ban.
        """

    @doc_parse.with_annotated_args
    @doc_parse.as_slash_command()
    async def unban_user(ctx: tanjun.abc.Context, user: annotations.User, reason: str = None) -> None:
        """Unban a user from this guild.

        :param user: The user to unban.
        :param reason: The reason for unbanning them.
        """


def with_annotated_args_typed_dict_example():
    class BulkMessagOptions(typing.TypedDict, total=False):
        """Reused bulk message command options.

        Parameters
        ----------
        count
            The amount of messages to target.
        regex
            A regular expression to match against message contents.
        """

        count: annotations.Int
        regex: annotations.Str

    @doc_parse.with_annotated_args
    @doc_parse.as_slash_command()
    async def delete_messages(
        ctx: tanjun.abc.Context, reason: str = None, **kwargs: typing.Unpack[BulkMessagOptions]
    ) -> None:
        """Toggle this setting for a user.

        Parameters
        ----------
        reasom
            Why you're bulk deleting these messages.
        """


def slash_command_group_example():
    help_group = doc_parse.slash_command_group("help", "get help")

    @tanjun.with_str_slash_option("command_name", "command name")
    @help_group.as_sub_command
    async def help(ctx: tanjun.abc.SlashContext, command_name: str) -> None:
        """Get help with a command."""

    @help_group.as_sub_command
    async def me(ctx: tanjun.abc.SlashContext) -> None:
        """Help me."""

    component = tanjun.Component().add_slash_command(help_group)
