# Usage

### Doc parse

##### as_slash_command

[tanchan.doc_parse][] exposes two methods which help with declaring slash commands:

```py
--8<-- "./docs_src/usage.py:16:31"
```

[tanchan.doc_parse.as_slash_command][] acts as an extension to [tanjun.as_slash_command][]
which uses the function's name as the command's name and the first line of its docstring
as the command's description.

##### with_annotated_args

```py
--8<-- "./docs_src/usage.py:35:89"
```

[tanchan.doc_parse.with_annotated_args][] uses the functionality exposed in [tanjun.annotations][]
but with the added feature that slash command option descriptions are parsed from the docstring.
This supports Google's doc style, NumPy's doc style, and Sphinx's "reST" doc style.

### Commands

Tan-chan provides several Tanjun commands which rely on the separate Yuyo
components library. To ensure a compatible Yuyo version is present you
should install Tan-chan with the `tanchan[yuyo]` install flag.

`"tanchan.components"` can be passed to
[Client.load_modules][tanjun.abc.Client.load_modules] as a shorthand to
add all of these commands and component handlers to a bot at once.

!!! note
    Any command config should be added the Tanjun client before the commands
    are loaded.

##### Help command

Tan-chan implements help commands which give users more information about
the commands loaded in a bot.

The message command this introduces can be called as either `{prefix}help` to
get a list of all available commands or as `{prefix}help {command name}` to get
more information about a specific command. Commands are grouped by the name of
their linked component by default so it's important to make sure you're passing
legible `name=`s to
[tanjun.Component.\_\_init\_\_][tanjun.components.Component.__init__].

By default slash command functionality is turned off but this can be enabled
using [tanchan.components.config.HelpConfig][].

These commands can be added to a bot by calling
[Client.load_modules][tanjun.abc.Client.load_modules] with
`"tanchan.components.help"`.

##### Eval command

Tan-chan implements eval commands which allow bot owners to dynamically
evaluate code in the bot's runtime.

The message command this introduces can be called simply by sending
`{prefix}eval` followed by a markdown codeblock of the code to execute.

The slash eval command isn't included by default but this can be set to be
declared globally or for specific guilds using
[tanchan.components.config.EvalConfig][] and its relevant `eval_guild_ids`
option.

These commands can be added to a bot by calling
[Client.load_modules][tanjun.abc.Client.load_modules] with
`"tanchan.components.eval"`.
