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
"""Internal utility classes and functions used by Tanchan."""
from __future__ import annotations

__all__: list[str] = ["MaybeLocalised", "inspect"]

import typing

from .localisation import MaybeLocalised
from .vendor import inspect

if typing.TYPE_CHECKING:
    from collections import abc as collections

    import typing_extensions
    from alluka import abc as alluka
    from tanjun import abc as tanjun

    class _WrappedProto(typing.Protocol):
        wrapped_command: typing.Optional[tanjun.ExecutableCommand[typing.Any]]

    _T = typing.TypeVar("_T")
    _CommandT = typing.TypeVar("_CommandT", bound=tanjun.ExecutableCommand[typing.Any])


def _has_wrapped(value: typing.Any, /) -> typing_extensions.TypeGuard[_WrappedProto]:
    try:
        value.wrapped_command

    except AttributeError:
        return False

    return True


def apply_to_wrapped(
    command: _CommandT,
    callback: collections.Callable[[tanjun.ExecutableCommand[typing.Any]], object],
    /,
    *,
    follow_wrapped: bool = True,
) -> _CommandT:
    """Apply a callback to all the commands in a decorator call chain.

    Parameters
    ----------
    command
        The top-level command object.
    callback
        Callback each wrapped command should be passed to.
    return_value
        Value to return from this function call.
    follow_wrapped
        Whether this should apply the callback to wrapped commands.
    """
    if follow_wrapped:
        wrapped = command.wrapped_command if _has_wrapped(command) else None

        while wrapped:
            callback(wrapped)
            wrapped = wrapped.wrapped_command if _has_wrapped(wrapped) else None

    return command


def get_or_set_dep(client: alluka.Client, type_: type[_T], callback: collections.Callable[[], _T]) -> _T:
    """Get a type dependency from a client or default to creating it."""
    if (value := client.get_type_dependency(type_, default=None)) is not None:
        return value

    value = callback()
    client.set_type_dependency(type_, value)
    return value
