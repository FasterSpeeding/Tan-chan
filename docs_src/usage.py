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

# pyright: reportUnusedFunction=none


def doc_parse_example() -> None:
    import tanjun

    from tanchan import doc_parse

    # This command will show up as "meow" in the command menu
    @doc_parse.as_slash_command()
    async def meow(ctx: tanjun.abc.SlashContext) -> None:
        """Meow command's description."""

    get_group = tanjun.slash_command_group("get", "Get command group")

    # This command will show up as "get user" in the command menu
    @get_group.with_command
    @doc_parse.as_slash_command()
    async def user(ctx: tanjun.abc.SlashContext) -> None:
        """Get a user."""


def as_slash_command_example() -> None:
    from typing import Annotated
    from typing import Optional

    import tanjun
    from tanjun import annotations

    from tanchan import doc_parse

    # Google's doc style.
    @doc_parse.with_annotated_args
    @doc_parse.as_slash_command()
    async def ban(
        ctx: tanjun.abc.SlashContext,
        user: annotations.User,
        reason: Optional[Annotated[annotations.Int, annotations.Length(460)]] = None,
    ) -> None:
        """Ban a user from this guild.

        Args:
            user: The user to ban from this guild.
            reason: The reason for the ban.
                If not provided then a generic reason will be used.
        """

    # NumPy's doc style.
    @doc_parse.with_annotated_args
    @doc_parse.as_slash_command()
    async def kick(
        ctx: tanjun.abc.SlashContext,
        member: annotations.Member,
        reason: Optional[Annotated[annotations.Int, annotations.Length(460)]] = None,
    ) -> None:
        """Kick a member from this guild.

        Parameters
        ----------
        member
            The guild member to kick.
        reason
            The reason for the kick.
            If not provided then a generic reason will be used.
        """

    # Sphinx's "reST" doc style.
    @doc_parse.with_annotated_args
    @doc_parse.as_slash_command()
    async def echo(
        ctx: tanjun.abc.SlashContext, content: annotations.Str, channel: Optional[annotations.Channel] = None
    ) -> None:
        """Make the bot echo a message.

        :param content: The message to echo.
        :param channel: The channel to echo to.
            If not provided then the current channel will be targeted.
        """
