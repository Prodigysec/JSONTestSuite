#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build/picojson"
revision=111c9be5188f7350c2eac9ddaedd8cca3d7bf394
archive="$build_dir/source.tar.gz"
checksum=671f89832a17e9e71398f80c0a326afa2ebe81f4c26d5a9992e1fcd0888ae151
mkdir -p "$build_dir"
if [ ! -f "$archive" ]; then
    curl --fail --silent --show-error --location \
        "https://github.com/kazuho/picojson/archive/$revision.tar.gz" -o "$archive.tmp"
    printf '%s  %s\n' "$checksum" "$archive.tmp" | sha256sum -c -
    mv "$archive.tmp" "$archive"
fi
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xzf "$archive" -C "$build_dir"
"${CXX:-c++}" -std=c++17 -O2 \
    -I "$build_dir/picojson-$revision" "$base_dir/test_picojson.cpp" \
    -o "$build_dir/test_picojson"
