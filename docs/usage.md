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
