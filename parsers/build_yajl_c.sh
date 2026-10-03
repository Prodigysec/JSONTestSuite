#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build/yajl-c"
revision=a0ecdde0c042b9256170f2f8890dd9451a4240aa
archive="$build_dir/source.tar.gz"
checksum=e1938d05fc48e2c3dcebb0c7dd61eb7d5e73817c0ce0bb88644a209f2d130daf
mkdir -p "$build_dir"
if [ ! -f "$archive" ]; then
    curl --fail --silent --show-error --location \
        "https://github.com/lloyd/yajl/archive/$revision.tar.gz" -o "$archive.tmp"
    mv "$archive.tmp" "$archive"
fi
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xzf "$archive" -C "$build_dir"
source_dir="$build_dir/yajl-$revision/src"
mkdir -p "$build_dir/include"
ln -sfn "$source_dir/api" "$build_dir/include/yajl"
"${CC:-cc}" -std=c99 -O2 -I "$source_dir" -I "$build_dir/include" \
    "$base_dir/test_yajl_c.c" "$source_dir/yajl.c" "$source_dir/yajl_lex.c" \
    "$source_dir/yajl_parser.c" "$source_dir/yajl_buf.c" "$source_dir/yajl_encode.c" \
    "$source_dir/yajl_alloc.c" -o "$build_dir/test_yajl_c"
