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
import typing

import pytest
import tanjun
from tanjun import annotations

import tanchan


def test_when_cant_detect_doc_style():
    @tanchan.doc_parse.as_slash_command()
    async def command(ctx: tanjun.abc.Context) -> None:
        """Description."""

    with pytest.raises(RuntimeError, match="Couldn't detect the docstring style"):
        tanchan.doc_parse.with_annotated_args(command)


def test_when_invalid_doc_style_passed():
    @tanchan.doc_parse.as_slash_command()
    async def command(ctx: tanjun.abc.Context) -> None:
        """Description."""

    with pytest.raises(ValueError, match="Unsupported docstring style 'catgirl-ml'"):
        tanchan.doc_parse.with_annotated_args(doc_style="catgirl-ml")(command)  # type: ignore


def test_as_slash_command_when_has_no_doc_string():
    async def command(ctx: tanjun.abc.Context) -> None:
        ...

    with pytest.raises(ValueError, match="Callback has no doc string"):
        tanchan.doc_parse.as_slash_command()(command)


def test_with_annotated_args_when_has_no_doc_string():
    @tanjun.as_slash_command("name", "description")
    async def command(ctx: tanjun.abc.Context) -> None:
        ...

    with pytest.raises(ValueError, match="Callback has no doc string"):
        tanchan.doc_parse.with_annotated_args()(command)


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

        Returns:
            Semantics. Kanye has lost it.
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
            Semantics. Kanye has lost it.

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

        Field
        ----
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

        Name
        ----

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
