#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build/amjson"
revision=1e282121c4ffa923740c9fe4477b1af8f2ef3f92
archive="$build_dir/source.tar.gz"
checksum=537f0e30aa50a9af6462cd384e8217fdd0085c44169bf81232af1ade360fab44
mkdir -p "$build_dir"
if [ ! -f "$archive" ]; then
    curl --fail --silent --show-error --location \
        "https://github.com/amwales-888/amjson/archive/$revision.tar.gz" -o "$archive.tmp"
    mv "$archive.tmp" "$archive"
fi
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xzf "$archive" -C "$build_dir"
source_dir="$build_dir/amjson-$revision"
"${CC:-cc}" -std=c99 -O2 -I "$source_dir" \
    "$base_dir/test_amjson.c" "$source_dir/amjson.c" -o "$build_dir/test_amjson"
