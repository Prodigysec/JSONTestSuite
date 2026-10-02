#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build"
revision=eb7860e0f58cf0829d35d70d0f5dea9fe38b1593
checksum=715affe9d34d52cce49553a3d15db5cbf111961c6f50044f2b07a670c6a2aab4
mkdir -p "$build_dir"
archive="$build_dir/jsonpp.tar.gz"
if [ ! -f "$archive" ]; then
    curl --fail --silent --show-error --location \
        "https://codeload.github.com/mikami-w/jsonpp/tar.gz/$revision" \
        -o "$archive.tmp"
    printf '%s  %s\n' "$checksum" "$archive.tmp" | sha256sum -c -
    mv "$archive.tmp" "$archive"
fi
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xzf "$archive" -C "$build_dir"
"${CXX:-c++}" -std=c++17 -O2 -I"$build_dir/jsonpp-$revision/src" \
    "$base_dir/main.cpp" -o "$build_dir/test_jsonpp"
printf 'Built %s\n' "$build_dir/test_jsonpp"
