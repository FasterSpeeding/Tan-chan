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

### Help command

Tan-chan implements commands which give users more information about the
commands loaded in a bot.

By default only the message command

These can be added to a bot by calling
[Client.load_modules][tanjun.clients.Client.load_modules] with
`"tanchan.components.help"` (or `"tanchan.components"` if you want all of
Tan-chan's commands).

### Eval command

Tan-chan implements an eval command which allows bot owners to dynamically evaluate
code in the bot's runtime.

By default only the

`eval_guild_ids`

These can be added to a bot by calling
[Client.load_modules][tanjun.clients.Client.load_modules] with
`"tanchan.components.eval"` (or `"tanchan.components"` if you want all of
Tan-chan's commands).
