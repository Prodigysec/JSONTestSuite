#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build"
archive="$build_dir/rl_json-v0.17.6.tar.gz"
checksum=c00da959d85ec1895ccf375f7551138d3a53a3d8af8387513b4370e007ca8655
mkdir -p "$build_dir"
if [ ! -f "$archive" ]; then
    curl --fail --silent --show-error --location \
        'https://github.com/RubyLane/rl_json/releases/download/v0.17.6/rl_json-v0.17.6.tar.gz' \
        -o "$archive.tmp"
    printf '%s  %s\n' "$checksum" "$archive.tmp" | sha256sum -c -
    mv "$archive.tmp" "$archive"
fi
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xzf "$archive" -C "$build_dir"
cd "$build_dir/rl_json-v0.17.6"
if [ -n "${TCL_CONFIG_DIR:-}" ]; then
    set -- --with-tcl="$TCL_CONFIG_DIR"
else
    set --
fi
if [ -n "${TCL_INCLUDE_DIR:-}" ]; then
    set -- "$@" --with-tclinclude="$TCL_INCLUDE_DIR"
fi
./configure "$@"
"${MAKE:-make}" binaries
printf 'Built %s\n' "$PWD/rl_json0.17.6.so"
