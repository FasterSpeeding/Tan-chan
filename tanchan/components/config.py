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
"""Configuration classes for Tanchan's command components."""
from __future__ import annotations

__all__: list[str] = ["Config", "EvalConfig", "HelpConfig"]

import typing

import attrs

if typing.TYPE_CHECKING:
    from collections import abc as collections

    from alluka import abc as alluka
    from tanjun import abc as tanjun


@attrs.define(kw_only=True, slots=False)
class EvalConfig:
    """Configuration for the eval commands.

    [EvalConfig.add_to_client][tanchan.components.config.EvalConfig.add_to_client]
    should be used to set this config.
    """

    eval_guild_ids: typing.Optional[collections.Collection[int]] = attrs.field(factory=tuple)
    """ID of the guilds the eval slash command should be declared in.

    If [None][] then this will be declared in every guild. Defaults to an empty
    sequences (so no guilds).
    """

    def add_to_client(self, client: typing.Union[alluka.Client, tanjun.Client], /) -> None:
        """Add this config to a Tanjun client.

        Parameters
        ----------
        client
            The client to add this config to.
        """
        client.set_type_dependency(EvalConfig, self)


@attrs.define(kw_only=True, slots=False)
class HelpConfig:
    """Configuration for the help commands.

    [HelpConfig.add_to_client][tanchan.components.config.HelpConfig.add_to_client]
    should be used to set this config.
    """

    # TODO: do i need to include the "Defaults to" doc sections here or is that already shown in the docs?
    enable_message_command: bool = True
    """Whether the help message command should be enabled.

    Defaults to [True][].
    """

    enable_slash_command: bool = False
    """Whether the help slash command should be enabled.

    Defaults to [False][].
    """

    include_slash_commands: bool = False
    """Whether slash commands should be included without the [with_help][yuyo.components.help.with_help] decorator.

    If [True][] then the command.description will be used as the description by
    default.

    Defaults to [False][].
    """

    include_message_commands: bool = True
    """Whether message commands should be included without the [with_help][yuyo.components.help.with_help] decorator.

    If [True][] then the command's callback docstring will be used as the
    description by default.

    Defaults to [True][].
    """

    def add_to_client(self, client: typing.Union[alluka.Client, tanjun.Client], /) -> None:
        client.set_type_dependency(HelpConfig, self)


@attrs.define(kw_only=True, slots=False)
class Config(EvalConfig, HelpConfig):
    """Full configuration for Tan-chan's commands and components.

    [Config.add_to_client][tanchan.components.config.Config.add_to_client]
    should be used to set this config.
    """

    def add_to_client(self, client: typing.Union[alluka.Client, tanjun.Client]) -> None:
        EvalConfig.add_to_client(self, client)
        HelpConfig.add_to_client(self, client)
