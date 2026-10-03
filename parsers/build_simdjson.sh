#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build/simdjson"
revision=8c512a3227ad322bfcb43c57c71fac67a83b5b8e
archive="$build_dir/source.tar.gz"
checksum=fd276ebb9101dbb615a086295f80dec26c08f80a01b332ec613a41ce0e0b0ecd
mkdir -p "$build_dir"
if [ ! -f "$archive" ]; then
    curl --fail --silent --show-error --location \
        "https://github.com/simdjson/simdjson/archive/$revision.tar.gz" \
        -o "$archive.tmp"
    printf '%s  %s\n' "$checksum" "$archive.tmp" | sha256sum -c -
    mv "$archive.tmp" "$archive"
fi
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xzf "$archive" -C "$build_dir"
source_dir="$build_dir/simdjson-$revision"
"${CXX:-c++}" -std=c++17 -O2 -I "$source_dir/singleheader" \
    "$base_dir/test_simdjson.cpp" "$source_dir/singleheader/simdjson.cpp" \
    -o "$build_dir/test_simdjson"
