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
from __future__ import annotations

__all__: list[str] = []

import typing

import hikari
import tanjun

if typing.TYPE_CHECKING:
    from collections import abc as collections


# TODO: expand tanjun's special casing of * to cover other command fields like responses here
_CommandTypes = typing.Literal["message", "message_menu", "slash", "user_menu"]
_TYPE_TO_STR: dict[typing.Optional[hikari.CommandType], _CommandTypes] = {
    hikari.CommandType.MESSAGE: "message_menu",
    hikari.CommandType.SLASH: "slash",
    hikari.CommandType.USER: "user_menu",
    None: "message",
}
_FieldTypes = typing.Literal["help.category", "help.name", "help.description"]


class MaybeLocalised:
    """Class used for handling name and description localisation."""

    __slots__ = ("default_value", "id", "_localise_id", "localised_values")

    def __init__(
        self,
        field_type: _FieldTypes,
        field: typing.Union[str, collections.Mapping[str, str], collections.Iterable[tuple[str, str]]],
        /,
        *,
        cmd_type: typing.Union[hikari.CommandType, None] = None,
        name: typing.Optional[str] = None,
    ) -> None:
        """Initialise an instance of MaybeLocalised.

        Parameters
        ----------
        field_type
            The type of field being localised.
        field
            The string value(s) to use for this value.

            If a [str][] is passed here then this will be used as the default
            value and the field's id for overloading it with the localiser.

            When a mapping is passed here, this should be a mapping of locales
            to values. If an "id" fieldis included then this will be used as the
            id for overloading it with the localiser and the first real value
            will be used as the default value.
        cmd_type
            The type of command this field is attached to.

            [None][] is used to represent message commands and this is ignored
            for `"help.category"` fields.
        name
            The name of the command this field is attached to.

            This is required for `"help.name"` and `"help.description"` fields
            and shouldn't be included for `"help.category"` fields as the
            default value is used.

        Raises
        ------
        RuntimeError
            If no default value is provided when `field` is a mapping.
        """
        if isinstance(field, str):
            self.default_value = field
            self.id: typing.Optional[str] = None
            self.localised_values: dict[str, str] = {}

        else:
            self.localised_values = dict(field)
            self.id = self.localised_values.pop("id", None)
            entry = self.localised_values.pop("default", None)
            if entry is None:
                entry = next(iter(self.localised_values.values()), None)

            if entry is None:
                raise RuntimeError(f"No default {field_type} given")

            self.default_value = entry

        if field_type == "help.category":
            if name is not None:
                raise RuntimeError("`name` cannot be passed for help.category fields")

            # TODO: tanjun needs to also accept using the raw ":" string for getting localisations
            self._localise_id = f"*:*:help.category:{self.default_value}"

        else:
            if name is None:
                raise ValueError(f"`name` must be passed for {field_type} fields")

            self._localise_id = f"{_TYPE_TO_STR[cmd_type]}:{name}:{field_type}"

    def to_hashable(self) -> str:
        """Make a string representation of this localised value.

        This is used for ensuring pagination states match.
        """
        if not self.localised_values:
            return self.default_value.split("\n", 1)[0]

        else:
            # Only care about the first line for pagination.
            descriptions = [(key, value.split("\n", 1)[0]) for key, value in self.localised_values.items()]
            return f"{self.default_value};{sorted(descriptions)!r}"

    def localise(self, locale: hikari.Locale, localiser: typing.Optional[tanjun.dependencies.AbstractLocaliser]) -> str:
        """Get the localised value for a context.

        Parameters
        ----------
        ctx
            The context to localise for.
        localiser
            The localiser to use for localising the response,
            if applicable.
        field_type
            The type of field being localised.
        field_name
            Name of the field being localised.

        Returns
        -------
        str
            The localised value or the default value.
        """
        if self.localised_values or localiser:
            if localiser and (field := localiser.localise(self._localise_id, locale)):
                return field

            return self.localised_values.get(locale, self.default_value)

        return self.default_value
