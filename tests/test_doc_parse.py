# -*- coding: utf-8 -*-
# BSD 3-Clause License
#
# Copyright (c) 2022-2023, Faster Speeding
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

# pyright: reportUnknownArgumentType=none
# Leads to too many false positives

import importlib.metadata
import typing
from unittest import mock

import hikari
import packaging.version
import pytest
import tanjun
from tanjun import annotations

import tanchan

TANJUN_VERSION = packaging.version.parse(importlib.metadata.version("hikari-tanjun"))


def test_when_cant_detect_doc_style():
    @tanchan.doc_parse.as_slash_command()
    async def command(ctx: tanjun.abc.Context) -> None:
        """Description.

        Not empty.
        """

    with pytest.raises(RuntimeError, match="Couldn't detect the docstring style"):
        tanchan.doc_parse.with_annotated_args(command)


@pytest.mark.parametrize("doc_style", [None, "google", "numpy", "reST"])
def test_when_only_description_in_docstring(doc_style: typing.Optional[typing.Literal["google", "numpy", "reST"]]):
    @tanchan.doc_parse.with_annotated_args(doc_style=doc_style)
    @tanchan.doc_parse.as_slash_command()
    async def aaaaaa_command(ctx: tanjun.abc.Context) -> None:
        """Meow description."""

    assert aaaaaa_command.name == aaaaaa_command.name == "aaaaaa_command"
    assert aaaaaa_command.description == aaaaaa_command.description == "Meow description."

    assert len(aaaaaa_command.build().options) == 0


def test_when_invalid_doc_style_passed():
    @tanchan.doc_parse.as_slash_command()
    async def command(ctx: tanjun.abc.Context) -> None:
        """Description.

        Not empty.
        """

    with pytest.raises(ValueError, match="Unsupported docstring style 'catgirl-ml'"):
        tanchan.doc_parse.with_annotated_args(doc_style="catgirl-ml")(command)  # type: ignore


def test_as_slash_command_when_has_no_doc_string():
    async def command(ctx: tanjun.abc.Context) -> None:
        ...

    with pytest.raises(ValueError, match="Callback has no doc string"):
        tanchan.doc_parse.as_slash_command()(command)


def test_as_slash_command_when_overrides_passed():
    @tanchan.doc_parse.as_slash_command(name="overridden_name", description="Meow meow meow meow!")
    async def command(ctx: tanjun.abc.Context) -> None:
        """Meow me meow."""

    builder = command.build()

    assert builder.name == command.name == "overridden_name"
    assert builder.description == command.description == "Meow meow meow meow!"


def test_as_slash_command_when_dict_overrides_passed():
    @tanchan.doc_parse.as_slash_command(
        name={hikari.Locale.BG: "background", "default": "hihi", hikari.Locale.EN_GB: "scott"},
        description={hikari.Locale.DA: "drum man", "default": "Meow meow!", hikari.Locale.EL: "salvador"},
    )
    async def command(ctx: tanjun.abc.Context) -> None:
        """Meow me meow."""

    builder = command.build()

    assert builder.name == command.name == "hihi"
    assert builder.name_localizations == {hikari.Locale.BG: "background", hikari.Locale.EN_GB: "scott"}
    assert builder.description == command.description == "Meow meow!"
    assert builder.description_localizations == {hikari.Locale.DA: "drum man", hikari.Locale.EL: "salvador"}


@pytest.mark.parametrize("doc_style", [None, "google", "numpy", "reST"])
def test_with_annotated_args_when_has_no_doc_string(
    doc_style: typing.Optional[typing.Literal["google", "numpy", "reST"]]
):
    @tanjun.as_slash_command("name", "description")
    async def command(ctx: tanjun.abc.Context) -> None:
        ...

    with pytest.raises(ValueError, match="Callback has no doc string"):
        tanchan.doc_parse.with_annotated_args(doc_style=doc_style)(command)


def test_google():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def eat_command(ctx: tanjun.abc.Context, meow: annotations.Int, nyaa: annotations.Str = "") -> None:
        """Meow meow meow.

        Args:
            meow: i'm ok man
            extra: yeet
            nyaa: go home
        """

    builder = eat_command.build()

    assert builder.name == eat_command.name == "eat_command"
    assert builder.description == eat_command.description == "Meow meow meow."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "meow"
    assert options[0].description == "i'm ok man"
    assert options[1].name == "nyaa"
    assert options[1].description == "go home"


def test_google_when_doc_style_explicitly_passed():
    @tanchan.doc_parse.with_annotated_args(doc_style="google")
    @tanchan.doc_parse.as_slash_command()
    async def eat_command(ctx: tanjun.abc.Context, meow: annotations.Int, nyaa: annotations.Str = "") -> None:
        """Meow meow meow.

        Args:
            meow: i'm ok man
            extra: yeet
            nyaa: go home
        """

    builder = eat_command.build()

    assert builder.name == eat_command.name == "eat_command"
    assert builder.description == eat_command.description == "Meow meow meow."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "meow"
    assert options[0].description == "i'm ok man"
    assert options[1].name == "nyaa"
    assert options[1].description == "go home"


def test_google_when_no_args():
    @tanchan.doc_parse.with_annotated_args(doc_style="google")
    @tanchan.doc_parse.as_slash_command()
    async def eat_command(ctx: tanjun.abc.Context) -> None:
        """Meow meow meow.

        Returns:
            meow: i'm ok man
        """

    assert len(eat_command.build().options) == 0


def test_google_with_type_hint():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def neat_command(ctx: tanjun.abc.Context, sicko: annotations.Int, echo: annotations.Str = "") -> None:
        """Meow meow.

        Args:
            sicko (int) : i'm ok girl
            extra (hikari.Users[Meow]): yeet
            echo (hikari.SnowflakeIsh[int]): go to work
        """

    builder = neat_command.build()

    assert builder.name == neat_command.name == "neat_command"
    assert builder.description == neat_command.description == "Meow meow."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "sicko"
    assert options[0].description == "i'm ok girl"
    assert options[1].name == "echo"
    assert options[1].description == "go to work"


def test_google_multi_line():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def meat_command(ctx: tanjun.abc.Context, sick: annotations.Int, stuff: annotations.Str = "") -> None:
        """Meow.

        Args:
            sick (int) : i'm ok girl
                meow meow
                echo echo
            extra : yeet
              echo yeet
            stuff (hikari.SnowflakeIsh[int]): go to work
                blep blep
        """

    builder = meat_command.build()

    assert builder.name == meat_command.name == "meat_command"
    assert builder.description == meat_command.description == "Meow."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "sick"
    assert options[0].description == "i'm ok girl meow meow echo echo"
    assert options[1].name == "stuff"
    assert options[1].description == "go to work blep blep"


def test_google_when_starts_on_next_line():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def beat_command(
        ctx: tanjun.abc.Context, respect: annotations.Bool, guillotine: typing.Optional[annotations.User] = None
    ) -> None:
        """Nyaa nyaa.

        Args:
            love:
                Should be ok to be
                insanely obvious.
            guillotine:
                Neon Genesis Evangelion gonna
                happen soon.
            respect:
                I'm literally just writing
                random words which come to
                mind.
        """

    builder = beat_command.build()

    assert builder.name == beat_command.name == "beat_command"
    assert builder.description == beat_command.description == "Nyaa nyaa."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "respect"
    assert options[0].description == "I'm literally just writing random words which come to mind."
    assert options[1].name == "guillotine"
    assert options[1].description == "Neon Genesis Evangelion gonna happen soon."


def test_google_with_other_section_after():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def command(ctx: tanjun.abc.Context, beep: annotations.Int, sheep: annotations.Str = "") -> None:
        """Nyaa.

        Args:
            beep: im
            sheep: a beep
            extra: yeet

        Raises:
            RuntimeError: VooDoo

        Returns:
            int: Semantics. Kanye has lost it.
        """

    builder = command.build()

    assert builder.name == command.name == "command"
    assert builder.description == command.description == "Nyaa."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "beep"
    assert options[0].description == "im"
    assert options[1].name == "sheep"
    assert options[1].description == "a beep"


def test_google_with_other_section_after_squashed():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def command(ctx: tanjun.abc.Context, beep: annotations.Int, sheep: annotations.Str = "") -> None:
        """Nyaa.

        Args:
            beep: im
            sheep: a beep
            extra: yeet
        Raises:
            RuntimeError: VooDoo
        Returns:
            int: Semantics. Kanye has lost it.
        """

    builder = command.build()

    assert builder.name == command.name == "command"
    assert builder.description == command.description == "Nyaa."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "beep"
    assert options[0].description == "im"
    assert options[1].name == "sheep"
    assert options[1].description == "a beep"


def test_google_with_other_section_before():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def catgirls(ctx: tanjun.abc.Context, beep: annotations.Int, sheep: annotations.Str = "") -> None:
        """Nyaa.

        Returns:
            Semantics: Kanye has lost it.

        Raises:
            RuntimeError: VooDoo

        Args:
            beep: im
            sheep: a beep
            extra: yeet
        """

    builder = catgirls.build()

    assert builder.name == catgirls.name == "catgirls"
    assert builder.description == catgirls.description == "Nyaa."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "beep"
    assert options[0].description == "im"
    assert options[1].name == "sheep"
    assert options[1].description == "a beep"


def test_google_with_other_section_before_squashed():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def catgirls(ctx: tanjun.abc.Context, beep: annotations.Int, sheep: annotations.Str = "") -> None:
        """Nyaa.

        Returns:
            Semantics: Kanye has lost it.
        Raises:
            RuntimeError: VooDoo
        Args:
            beep: im
            sheep: a beep
            extra: yeet
        """

    builder = catgirls.build()

    assert builder.name == catgirls.name == "catgirls"
    assert builder.description == catgirls.description == "Nyaa."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "beep"
    assert options[0].description == "im"
    assert options[1].name == "sheep"
    assert options[1].description == "a beep"


def test_google_trails_off():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def feet_command(ctx: tanjun.abc.Context, beep: annotations.Int, sheep: annotations.Str = "") -> None:
        """Nyaa.

        Args:
            beep: im
            sheep: a beep
            extra: yeet

        """

    builder = feet_command.build()

    assert builder.name == feet_command.name == "feet_command"
    assert builder.description == feet_command.description == "Nyaa."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "beep"
    assert options[0].description == "im"
    assert options[1].name == "sheep"
    assert options[1].description == "a beep"


def test_numpy():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def cc(
        ctx: tanjun.abc.Context, foo: annotations.Str, bar: typing.Optional[annotations.Ranged[0.23, 321.2]] = None
    ) -> None:
        """I am very gay.

        Parameters
        ----------
        foo : sex
            go home boss
        bar
            meowers
        unknown
            mexican
        """

    builder = cc.build()

    assert builder.name == cc.name == "cc"
    assert builder.description == cc.description == "I am very gay."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "foo"
    assert options[0].description == "go home boss"
    assert options[1].name == "bar"
    assert options[1].description == "meowers"


def test_numpy_when_doc_style_explicitly_passed():
    @tanchan.doc_parse.with_annotated_args(doc_style="numpy")
    @tanchan.doc_parse.as_slash_command()
    async def cc(
        ctx: tanjun.abc.Context, foo: annotations.Str, bar: typing.Optional[annotations.Ranged[0.23, 321.2]] = None
    ) -> None:
        """I am very gay.

        Parameters
        ----------
        foo : sex
            go home boss
        bar
            meowers
        unknown
            mexican
        """

    builder = cc.build()

    assert builder.name == cc.name == "cc"
    assert builder.description == cc.description == "I am very gay."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "foo"
    assert options[0].description == "go home boss"
    assert options[1].name == "bar"
    assert options[1].description == "meowers"


def test_numpy_when_no_parameters():
    @tanchan.doc_parse.with_annotated_args(doc_style="numpy")
    @tanchan.doc_parse.as_slash_command()
    async def cc(ctx: tanjun.abc.Context) -> None:
        """I am very gay.

        Returns
        -------
        int
            Voodoo baby.
        """

    assert len(cc.build().options) == 0


def test_numpy_ended_by_nameless_terminator_after():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def eep_command(ctx: tanjun.abc.Context, echo: annotations.Bool, zulu: annotations.Str = ""):
        """You're a catgirl; I know right (sleepy). [];';-o0-

        Parameters
        ----------
        echo : sex
            go home big boss
        zulu
            nyaners
        other
            japanese

        -----------
        meow the yeet
            woof
        yeet : int
            barf
        """

    builder = eep_command.build()

    assert builder.name == eep_command.name == "eep_command"
    assert builder.description == eep_command.description == "You're a catgirl; I know right (sleepy). [];';-o0-"

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "echo"
    assert options[0].description == "go home big boss"
    assert options[1].name == "zulu"
    assert options[1].description == "nyaners"


def test_numpy_ended_by_nameless_terminator_after_squashed():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def eep_command(ctx: tanjun.abc.Context, echo: annotations.Bool, zulu: annotations.Str = ""):
        """You're a catgirl; I know right (sleepy). [];';-o0-

        Parameters
        ----------
        echo : sex
            go home big boss
        zulu
            nyaners
        other
            japanese
        -----------
        meow the yeet
            woof
        yeet : int
            barf
        """

    builder = eep_command.build()

    assert builder.name == eep_command.name == "eep_command"
    assert builder.description == eep_command.description == "You're a catgirl; I know right (sleepy). [];';-o0-"

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "echo"
    assert options[0].description == "go home big boss"
    assert options[1].name == "zulu"
    assert options[1].description == "nyaners"


def test_numpy_after_named_section():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def aaaaaa(ctx: tanjun.abc.Context, meow: annotations.Int = 0, nyaa: annotations.Float = 123.312):
        """sleepers meow

        Returns
        -------
        yellow : meow
            Nom

        Parameters
        ----------
        meow : sex
            gimme gimme chocolate
        nope
            war moment
        nyaa
            other race
        """

    builder = aaaaaa.build()

    assert builder.name == aaaaaa.name == "aaaaaa"
    assert builder.description == aaaaaa.description == "sleepers meow"

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "meow"
    assert options[0].description == "gimme gimme chocolate"
    assert options[1].name == "nyaa"
    assert options[1].description == "other race"


def test_numpy_after_named_section_squashed():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def aaaaaa(ctx: tanjun.abc.Context, meow: annotations.Int = 0, nyaa: annotations.Float = 123.312):
        """sleepers meow

        Returns
        -------
        yellow : meow
            Nom
        Parameters
        ----------
        meow : sex
            gimme gimme chocolate
        nope
            war moment
        nyaa
            other race
        """

    builder = aaaaaa.build()

    assert builder.name == aaaaaa.name == "aaaaaa"
    assert builder.description == aaaaaa.description == "sleepers meow"

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "meow"
    assert options[0].description == "gimme gimme chocolate"
    assert options[1].name == "nyaa"
    assert options[1].description == "other race"


def test_numpy_ended_by_named_section():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def aaaaaa(ctx: tanjun.abc.Context, meow: annotations.Int = 0, nyaa: annotations.Float = 123.312):
        """sleepers meow

        Parameters
        ----------
        meow : sex
            gimme gimme chocolate
        nope
            war moment
        nyaa
            other race

        Returns
        -------
        yellow : meow
            Nom
        """

    builder = aaaaaa.build()

    assert builder.name == aaaaaa.name == "aaaaaa"
    assert builder.description == aaaaaa.description == "sleepers meow"

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "meow"
    assert options[0].description == "gimme gimme chocolate"
    assert options[1].name == "nyaa"
    assert options[1].description == "other race"


def test_numpy_ended_by_named_section_squashed():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def aaaaaa(ctx: tanjun.abc.Context, meow: annotations.Int = 0, nyaa: annotations.Float = 123.312):
        """sleepers meow

        Parameters
        ----------
        meow : sex
            gimme gimme chocolate
        nope
            war moment
        nyaa
            other race
        Returns
        -------
        yellow : meow
            Nom
        """

    builder = aaaaaa.build()

    assert builder.name == aaaaaa.name == "aaaaaa"
    assert builder.description == aaaaaa.description == "sleepers meow"

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "meow"
    assert options[0].description == "gimme gimme chocolate"
    assert options[1].name == "nyaa"
    assert options[1].description == "other race"


def test_numpy_with_other_parameters():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def cool_girl(ctx: tanjun.abc.Context, the: annotations.User, go: annotations.Int, cat: annotations.Member):
        """blep

        Parameters
        ----------
        pat: sex
            get regulated
        the
            meows and nyaas. yeet; [';#][]
        cat
            box

        Returns
        -------
        yellow : meow
            Nom

        Other Parameters
        ----------------
        go
            home
        nope
            yep
        """

    builder = cool_girl.build()

    assert builder.name == cool_girl.name == "cool_girl"
    assert builder.description == cool_girl.description == "blep"

    options = builder.options
    assert len(options) == 3
    assert options[0].name == "the"
    assert options[0].description == "meows and nyaas. yeet; [';#][]"
    assert options[1].name == "go"
    assert options[1].description == "home"
    assert options[2].name == "cat"
    assert options[2].description == "box"


def test_numpy_for_multi_line_descriptions():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def eep_command(
        ctx: tanjun.abc.Context, foo: annotations.Str, bar: typing.Optional[annotations.Ranged[0.23, 321.2]] = None
    ) -> None:
        """I am very catgirly.

        Parameters
        ----------
        foo : sex
            go home boss
            nyaa extra
        bar
            meowers in the streets,
            nyanners in the sheets
        unknown
            mexican
            and japanese
        """

    builder = eep_command.build()

    assert builder.name == eep_command.name == "eep_command"
    assert builder.description == eep_command.description == "I am very catgirly."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "foo"
    assert options[0].description == "go home boss nyaa extra"
    assert options[1].name == "bar"
    assert options[1].description == "meowers in the streets, nyanners in the sheets"


def test_rest():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def sphinx_command(
        ctx: tanjun.abc.Context, cat: annotations.User, pan: typing.Optional[annotations.Channel] = None
    ) -> None:
        """I love cats.

        :param cat: The user of my dreams.
        :type cat: hikari.User
        :param not_found: Not found parameter.
        :type not_found: NoReturn
        :param pan: The channel of my dreams.
        :type pan: hikari.PartialChannel
        """

    builder = sphinx_command.build()

    assert builder.name == sphinx_command.name == "sphinx_command"
    assert builder.description == sphinx_command.description == "I love cats."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "cat"
    assert options[0].description == "The user of my dreams."
    assert options[1].name == "pan"
    assert options[1].description == "The channel of my dreams."


def test_rest_when_doc_style_explicitly_passed():
    @tanchan.doc_parse.with_annotated_args(doc_style="reST")
    @tanchan.doc_parse.as_slash_command()
    async def a_command(
        ctx: tanjun.abc.Context, user: annotations.User, channel: typing.Optional[annotations.Channel] = None
    ) -> None:
        """I love meowers.

        :param user: The meow.
        :type user: hikari.Member
        :param not_found: Not found.
        :type not_found: NoReturn
        :param channel: The cat.
        :type channel: hikari.GuildChannel
        """

    builder = a_command.build()

    assert builder.name == a_command.name == "a_command"
    assert builder.description == a_command.description == "I love meowers."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "user"
    assert options[0].description == "The meow."
    assert options[1].name == "channel"
    assert options[1].description == "The cat."


def test_rest_with_no_type_hints():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def b_command(
        ctx: tanjun.abc.Context, beep: annotations.User, op: typing.Optional[annotations.Channel] = None
    ) -> None:
        """I love nyans.

        :param beep: Nyanners.
        :param not_found: Not found.
        :param op: The catty cat.
        """

    builder = b_command.build()

    assert builder.name == b_command.name == "b_command"
    assert builder.description == b_command.description == "I love nyans."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "beep"
    assert options[0].description == "Nyanners."
    assert options[1].name == "op"
    assert options[1].description == "The catty cat."


def test_rest_for_multi_line_descriptions():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def sphinx_command(
        ctx: tanjun.abc.Context, member: annotations.Member, state: typing.Optional[annotations.Bool] = None
    ) -> None:
        """I love cats.

        :param member: The member of my dreams.
            If you sleep, if you sleep.
        :type member: hikari.Member
        :param state: The state of my dreams.
            If I bool, if I bool.
        :type state: bool
        :param not_found: Not found parameter.
        :type not_found: NoReturn
        """

    builder = sphinx_command.build()

    assert builder.name == sphinx_command.name == "sphinx_command"
    assert builder.description == sphinx_command.description == "I love cats."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "member"
    assert options[0].description == "The member of my dreams. If you sleep, if you sleep."
    assert options[1].name == "state"
    assert options[1].description == "The state of my dreams. If I bool, if I bool."


def test_rest_when_starts_on_next_line():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def sphinx_command(
        ctx: tanjun.abc.Context, me: annotations.Channel, aaa: typing.Optional[annotations.Int] = None
    ) -> None:
        """I love cats.

        :param not_found: Not found parameter.
        :type not_found: NoReturn
        :param me:
            Meow, I'm a kitty cat and I dance
            dance and dance and I dance dance dance.
        :type member: hikari.PartialChannel
        :param aaa:
            Cats I'm a kitty girl and I Nyaa Nyaa
            Nyaa and i Nyaa Nyaa Nyaa.
        :type aaa: int
        """

    builder = sphinx_command.build()

    assert builder.name == sphinx_command.name == "sphinx_command"
    assert builder.description == sphinx_command.description == "I love cats."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "me"
    assert options[0].description == "Meow, I'm a kitty cat and I dance dance and dance and I dance dance dance."
    assert options[1].name == "aaa"
    assert options[1].description == "Cats I'm a kitty girl and I Nyaa Nyaa Nyaa and i Nyaa Nyaa Nyaa."


def test_rest_trails_off():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def sphinx_command(
        ctx: tanjun.abc.Context, member: annotations.Member, state: typing.Optional[annotations.Bool] = None
    ) -> None:
        """I love cats.

        :param member: The member of my dreams.
            If you sleep, if you sleep.
        :type member: hikari.Member
        :param state: The state of my dreams.
            If I bool, if I bool.
        :type state: bool
        :param not_found: Not found parameter.
        :type not_found: NoReturn

        """

    builder = sphinx_command.build()

    assert builder.name == sphinx_command.name == "sphinx_command"
    assert builder.description == sphinx_command.description == "I love cats."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "member"
    assert options[0].description == "The member of my dreams. If you sleep, if you sleep."
    assert options[1].name == "state"
    assert options[1].description == "The state of my dreams. If I bool, if I bool."


def test_rest_trails_off_with_multi_line_description():
    @tanchan.doc_parse.with_annotated_args()
    @tanchan.doc_parse.as_slash_command()
    async def sphinx_command(
        ctx: tanjun.abc.Context, member: annotations.Member, state: typing.Optional[annotations.Bool] = None
    ) -> None:
        """I love cats.

        :param member: The member of my dreams.
            If you sleep, if you sleep.
        :type member: hikari.Member
        :param state: The state of my dreams.
            If I bool, if I bool.
        :type state: bool
        :param not_found: Not found parameter.
        :type not_found: NoReturn
            Meow meow.

        """

    builder = sphinx_command.build()

    assert builder.name == sphinx_command.name == "sphinx_command"
    assert builder.description == sphinx_command.description == "I love cats."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "member"
    assert options[0].description == "The member of my dreams. If you sleep, if you sleep."
    assert options[1].name == "state"
    assert options[1].description == "The state of my dreams. If I bool, if I bool."


TANJUN_SUPPORTS_TYPED_DICT = TANJUN_VERSION >= packaging.version.parse("2.12.0")


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_parses_unpacked_typed_dict_auto_detect_google():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_parses_unpacked_typed_dict_auto_detect_numpy():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_parses_unpacked_typed_dict_auto_detect_rest():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_parses_unpacked_typed_dict_passed_format():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_when_only_unpacked_typed_dict_has_doc():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_ignores_unparsable_typed_dict():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_ignores_docless_typed_dict():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_errors_when_neither_typed_dict_nor_function_have_doc():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_errors_when_typed_dict_doc_has_no_params_and_function_has_no_doc():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_errors_when_unpack_isnt_typed_dict():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_errors_when_kwargs_type_isnt_unpacked():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_errors_ignores_unpacked_typed_dict_for_varargs():
    ...


@pytest.mark.skipif(not TANJUN_SUPPORTS_TYPED_DICT, reason="Tanjun version doesn't support typed dict parsing")
def test_errors_ignores_unpacked_typed_dict_for_normal_arg():
    ...


class TestSlashCommandGroup:
    def test_as_sub_command(self):
        group = tanchan.doc_parse.SlashCommandGroup("name", "description")

        @group.as_sub_command()
        async def super_name_nyaa(ctx: tanjun.abc.Context):
            """Command me meowy."""

        assert super_name_nyaa in group.commands
        assert super_name_nyaa.name == "super_name_nyaa"
        assert super_name_nyaa.description == "Command me meowy."
        assert super_name_nyaa.defaults_to_ephemeral is None

    @pytest.mark.parametrize(
        "wrapped_type", [tanjun.abc.MenuCommand, tanjun.abc.MessageCommand, tanjun.abc.SlashCommand]
    )
    def test_as_sub_command_when_wrapping_other_command(self, wrapped_type: type[typing.Any]):
        def meow_callback() -> None:
            """Meow indeed mr Bond."""

        group = tanchan.doc_parse.SlashCommandGroup("name", "description")
        wrapped_cmd = mock.MagicMock(wrapped_type, callback=meow_callback)

        command = group.as_sub_command()(wrapped_cmd)

        assert command.name == "meow_callback"
        assert command.description == "Meow indeed mr Bond."
        assert command.callback is meow_callback

    def test_as_sub_command_when_optional_parameters_passed(self):
        group = tanchan.doc_parse.SlashCommandGroup("name", "description")

        @group.as_sub_command(name="xd_nuz", description="descriptor", default_to_ephemeral=True)
        async def super_nyaa(ctx: tanjun.abc.Context):
            """Command meow."""

        assert super_nyaa.name == "xd_nuz"
        assert super_nyaa.description == "descriptor"
        assert super_nyaa.defaults_to_ephemeral is True

    def test_as_sub_command_when_has_no_doc_string(self):
        group = tanchan.doc_parse.SlashCommandGroup("name", "description")

        async def command(ctx: tanjun.abc.Context) -> None:
            ...

        with pytest.raises(ValueError, match="Callback has no doc string"):
            group.as_sub_command()(command)

    def test_as_sub_command_when_dict_overrides_passed(self):
        group = tanchan.doc_parse.SlashCommandGroup("name", "description")

        @group.as_sub_command(
            name={hikari.Locale.EN_GB: "hhh", hikari.Locale.FR: "hon_hon"},
            description={hikari.Locale.HR: "H", hikari.Locale.DE: "nein"},
        )
        async def super_(ctx: tanjun.abc.Context):
            """meow."""

        assert super_.name == "hhh"
        assert super_.name_localisations == {hikari.Locale.EN_GB: "hhh", hikari.Locale.FR: "hon_hon"}
        assert super_.description == "H"
        assert super_.description_localisations == {hikari.Locale.HR: "H", hikari.Locale.DE: "nein"}

    def test_make_sub_group(self):
        group = tanchan.doc_parse.slash_command_group("echo", "meow")

        sub_group = group.make_sub_group("aaaa", "very descript of you Sherlock")

        assert isinstance(sub_group, tanchan.doc_parse.SlashCommandGroup)
        assert sub_group in group.commands
        assert sub_group.name == "aaaa"
        assert sub_group.description == "very descript of you Sherlock"
        assert sub_group.defaults_to_ephemeral is None

    def test_make_sub_group_when_optional_args_passed(self):
        group = tanchan.doc_parse.slash_command_group("echo", "meow")

        sub_group = group.make_sub_group("fancy", "music time!!!", default_to_ephemeral=True)

        assert isinstance(sub_group, tanchan.doc_parse.SlashCommandGroup)
        assert sub_group in group.commands
        assert sub_group.name == "fancy"
        assert sub_group.description == "music time!!!"
        assert sub_group.defaults_to_ephemeral is True


def test_slash_command_group():
    group = tanchan.doc_parse.slash_command_group("name_me", "Describe me")

    assert group.name == "name_me"
    assert group.description == "Describe me"
    assert group.default_member_permissions is None
    assert group.is_dm_enabled is None
    assert group.is_global is True


def test_slash_command_group_with_optional_args():
    group = tanchan.doc_parse.slash_command_group(
        "name_her", "Describe her", default_member_permissions=123321, dm_enabled=True, is_global=False
    )

    assert group.name == "name_her"
    assert group.description == "Describe her"
    assert group.default_member_permissions == 123321
    assert group.is_dm_enabled is True
    assert group.is_global is False
