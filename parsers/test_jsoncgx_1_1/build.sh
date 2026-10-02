#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build"
archive="$build_dir/jsoncgx-1.1.tar.gz"
checksum=1b3b736e6f7c4092dd5b8db2547cc47c78e2b577a436ddcff34214dc551f94a6
mkdir -p "$build_dir"
if [ ! -f "$archive" ]; then
    curl --fail --silent --show-error --location \
        'https://files.pythonhosted.org/packages/source/j/jsoncgx/jsoncgx-1.1.tar.gz' \
        -o "$archive.tmp"
    printf '%s  %s\n' "$checksum" "$archive.tmp" | sha256sum -c -
    mv "$archive.tmp" "$archive"
fi
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xzf "$archive" -C "$build_dir"
printf 'Prepared %s\n' "$build_dir/jsoncgx-1.1"
