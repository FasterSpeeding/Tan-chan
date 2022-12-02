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

import tanjun
from tanjun import annotations

import tanchan


def test():
    @tanchan.doc_parse.with_annotated_args(follow_wrapped=True)
    @tanchan.doc_parse.as_slash_command()
    async def eat_command(
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

    builder = eat_command.build()

    assert builder.name == eat_command.name == "eat_command"
    assert builder.description == eat_command.description == "I am very gay."

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "foo"
    assert options[0].description == "go home boss"
    assert options[1].name == "bar"
    assert options[1].description == "meowers"


def test_ended_by_nameless_terminator_after():
    @tanchan.doc_parse.with_annotated_args(follow_wrapped=True)
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
        """  # noqa: D400

    builder = eep_command.build()

    assert builder.name == eep_command.name == "eep_command"
    assert builder.description == eep_command.description == "You're a catgirl; I know right (sleepy). [];';-o0-"

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "echo"
    assert options[0].description == "go home big boss"
    assert options[1].name == "zulu"
    assert options[1].description == "nyaners"


def test_ended_by_named_section():
    @tanchan.doc_parse.with_annotated_args(follow_wrapped=True)
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
        """  # noqa: D400, D403

    builder = aaaaaa.build()

    assert builder.name == aaaaaa.name == "aaaaaa"
    assert builder.description == aaaaaa.description == "sleepers meow"

    options = builder.options
    assert len(options) == 2
    assert options[0].name == "meow"
    assert options[0].description == "gimme gimme chocolate"
    assert options[1].name == "nyaa"
    assert options[1].description == "other race"


def test_with_other_parameters():
    @tanchan.doc_parse.with_annotated_args(follow_wrapped=True)
    @tanchan.doc_parse.as_slash_command()
    async def cool_girl(ctx: tanjun.abc.Context, the: annotations.User, go: annotations.Int, cat: annotations.Member):
        """blep

        Parameters
        ----------
        pat : sex
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
        """  # noqa: D400, D403

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
