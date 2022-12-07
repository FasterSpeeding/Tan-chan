# -*- coding: utf-8 -*-
# BSD 3-Clause License
#
# Copyright (c) 2022, Faster Speeding
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


def test_doc_prase_as_slash_command():
    import tanjun

    from tanchan import doc_parse

    # This command will show up as "meow" in the command menu
    @doc_parse.as_slash_command()
    async def meow(ctx: tanjun.abc.SlashContext) -> None:
        """Meow command's description."""
        ...

    get_group = tanjun.slash_command_group("get", "Get command group")

    # This command will show up as "get user" in the command menu
    @get_group.with_command
    @doc_parse.as_slash_command()
    async def user(ctx: tanjun.abc.SlashContext) -> None:
        """Get a user."""
        ...

    build = meow.build()

    assert meow.name == build.name == "meow"
    assert meow.description == build.description == "Meow command's description."
    assert len(build.options) == 0

    build = user.build()
    assert user.name == build.name == "user"
    assert user.description == build.description == "Get a user."
    assert len(build.options) == 0
    assert user in get_group.commands


def test_doc_parse_with_annotated_args():
    import typing

    import tanjun
    from tanjun import annotations

    from tanchan import doc_parse

    # Google's doc style.
    @doc_parse.with_annotated_args
    @doc_parse.as_slash_command()
    async def ban(
        ctx: tanjun.abc.SlashContext, user: annotations.User, reason: typing.Optional[annotations.Length[460]] = None
    ) -> None:
        """Ban a user from this guild.

        Args:
            user: The user to ban from this guild.
            reason: The reason for the ban.
                If not provided then a generic reason will be used.
        """  # noqa: D407

    # NumPy's doc style.
    @doc_parse.with_annotated_args
    @doc_parse.as_slash_command()
    async def kick(
        ctx: tanjun.abc.SlashContext,
        member: annotations.Member,
        reason: typing.Optional[annotations.Length[460]] = None,
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
        ctx: tanjun.abc.SlashContext, content: annotations.Str, channel: typing.Optional[annotations.Channel] = None
    ) -> None:
        """Make the bot echo a message.

        :param content: The message to echo.
        :param channel: The channel to echo to.
            If not provided then the current channel will be targeted.
        """

    build = ban.build()

    assert ban.name == build.name == "ban"
    assert ban.description == build.description == "Ban a user from this guild."
    assert len(build.options) == 2
    assert build.options[0].name == "user"
    assert build.options[0].description == "The user to ban from this guild."
    assert build.options[1].name == "reason"
    assert build.options[1].description == (
        "The reason for the ban. If not provided then a generic reason will be used."
    )

    build = kick.build()

    assert kick.name == build.name == "kick"
    assert kick.description == build.description == "Kick a member from this guild."
    assert len(build.options) == 2
    assert build.options[0].name == "member"
    assert build.options[0].description == "The guild member to kick."
    assert build.options[1].name == "reason"
    assert build.options[1].description == (
        "The reason for the kick. If not provided then a generic reason will be used."
    )

    build = echo.build()

    assert echo.name == build.name == "echo"
    assert echo.description == build.description == "Make the bot echo a message."
    assert len(build.options) == 2
    assert build.options[0].name == "content"
    assert build.options[0].description == "The message to echo."
    assert build.options[1].name == "channel"
    assert (
        build.options[1].description
        == "The channel to echo to. If not provided then the current channel will be targeted."
    )
