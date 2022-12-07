# Usage

## Doc parse

[tanchan.doc_parse][] exposes two methods which help with declaring slash commands:

```py
import tanjun
from tanchan import docparse


# This command will show up as "meow" in the command menu
@docprase.as_slash_command()
async def meow(ctx: tanjun.abc.SlashContext) -> None:
    """Meow command's description."""
    raise NotImplementedError


get_group = tanjun.slash_command_group("get", "Get command group")


# This command will show up as "get user" in the command menu
@get_group.with_command
@docparse.as_slash_command()
async def user(ctx: tanjun.abc.SlashContext) -> None:
    """Get a user."""
    raise NotImplementedError
```

[tanchan.doc_parse.as_slash_command][] acts as an extension to [tanjun.as_slash_command][]
which uses the function's name as the command's name and the first line of its docstring
as the command's description.


```py
import tanjun
from tanchan import docparse
from tanjun import annotations


# Google'S doc style.
@docprase.with_annotated_args
@docparse.as_slash_command()
async def ban(
    ctx: tanjun.abc.SlashContext,
    user: annotations.User,
    reason: annotations.Length[460] | None = None
) -> None:
    """Kick a member from this guild.

    Args:
        user
            The user to ban from this guild.
        reason
            The reason for the ban.
            If not provided then a generic reason will be used.
    """


# NumPy's doc style.
@docprase.with_annotated_args
@docparse.as_slash_command()
async def kick(
    ctx: tanjun.abc.SlashContext,
    user: annotations.Member,
    reason: annotations.Length[460] | None = None
) -> None:
    """Kick a member from this guild.

    Parameters
    ----------
    user
        The guild member to kick
    reason
        The reason for the kick.
        If not provided then a generic reason will be used.
    """


# Sphinx's "reST" doc style.
@docprase.with_annotated_args
@docparse.as_slash_command()
async def echo(
    ctx: tanjun.abc.SlashContext,
    content: annotations.Str,
    channel: annotations.Channel | None = None
) -> None:
    """Make the bot echo a message.

    :param content: The message to echo.
    :param private: The channel to echo to.
        If not provided then the current channel will be targeted.
    """
```


[tanchan.doc_parse.with_annotated_args][] uses the functionality exposed in [tanjun.annotations][]
but with the added feature that slash command option descriptions are parsed from the docstring.
This supports Google's doc style, NumPy's doc style, and Sphinx's "reST" doc style.
