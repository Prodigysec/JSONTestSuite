# Ruby JSON adapter

The `Ruby` registry entry invokes `/usr/bin/env ruby parsers/test_json.rb FILE`.
It uses Ruby's [JSON library](https://github.com/ruby/json), reads the entire file
with `File.read`, and calls `JSON.parse` with default options. It does not select
a streaming mode or preprocess the input. A successful parse exits `0`, including
when JSON `null` produces Ruby `nil`; `JSON::ParserError` exits `1`.

Install Ruby with its JSON library; the adapter itself needs no build step.
From the repository root, check versions and invoke it with:

```sh
ruby -rjson -e 'puts RUBY_DESCRIPTION; puts JSON::VERSION'
ruby parsers/test_json.rb test_parsing/y_structure_lonely_null.json
```

The registry requires a POSIX environment with `/usr/bin/env` and `ruby` on PATH.
Validation used Linux x86_64, Ruby **3.2.3**, and JSON **2.6.3**, from Ubuntu 24.04
packages `ruby3.2` and `libruby3.2`, both version `3.2.3-1ubuntu0.24.04.8`.
The packages were extracted into a temporary directory without system
installation; `RUBYLIB` and `LD_LIBRARY_PATH` pointed into that directory, and
`RUBYOPT=--disable-gems` disabled gem discovery. No other Ruby versions or
platforms were tested. The versionless registry name is not version detection.

The adapter retains the installed library's default limits and extension
behavior; it is not a strict reference validator. Historical Ruby/JSON releases
that required `quirks_mode` for scalar inputs are not validated by this change.
Unhandled file/runtime/dependency errors can still exit `1`; check dependencies
and diagnostics before interpreting such failures as JSON rejection.

The null fix applies Jean Boussier's (`byroot`) change from
[upstream PR #145](https://github.com/nst/JSONTestSuite/pull/145), commit
[`c1126847737c02a842f9767ba6a5823813b7e618`](https://github.com/nst/JSONTestSuite/commit/c1126847737c02a842f9767ba6a5823813b7e618),
without changes to the proposed adapter patch. This removes the obsolete option,
the nil-as-failure check, and the parsed-value debug print. The local addition is
regression coverage and this documentation; no dependencies or licenses change.

`tests/test_ruby_adapter.py` exercises acceptance (including `null`, `false`, and
`0`), rejection, trailing input, malformed bytes, and implementation-dependent
cases, with a five-second subprocess timeout. Tests use `ruby` or `ruby3.2` on
PATH, and explicitly skip if neither is available. Run them with the rest of
the suite:

```sh
python3 -B -m unittest discover -s tests -v
```
