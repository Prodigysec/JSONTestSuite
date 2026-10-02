# Using the corpus without parser binaries

The authoritative parsing fixtures live in `test_parsing/`. The `y_`, `n_`,
and `i_` prefixes mean expected acceptance, expected rejection, and
implementation-dependent acceptance or rejection, respectively. A crash or
timeout is never a successful result for an `i_` fixture. `test_transform/`
contains value and serialization examples; the current runner does not execute
them as transformation tests. Treat each fixture as bytes, including missing
final newlines, invalid UTF-8, and literal NULs.

From a normal checkout, make a small source snapshot with Git, make, and gzip:

```sh
make corpus-archive
tar -tzf dist/JSONTestSuite-corpus-*.tar.gz | head
```

The archive is generated from committed `HEAD`, not uncommitted or untracked
fixture changes. It contains the two fixture directories and `LICENSE`, with
their original relative paths and bytes. Share that archive as an artifact if
a Git submodule is not required. The project does not publish a separate
corpus-only Git repository.

For a Git working tree with only the fixture directories and root-level files,
use a partial clone and sparse checkout:

```sh
git clone --filter=blob:none --sparse https://github.com/Prodigysec/JSONTestSuite.git
cd JSONTestSuite
git sparse-checkout set test_parsing test_transform
```

The `--filter=blob:none` option asks the server to defer file contents until
needed; `--sparse` and `git sparse-checkout set` keep `parsers/` and `results/`
out of the working tree. Cone-mode sparse checkout also includes root-level
files. This is still a checkout of the full repository, not a separate
fixture-only repository or submodule. To pin test cases, check out a specific
commit and record its hash alongside the parser version and mode.
