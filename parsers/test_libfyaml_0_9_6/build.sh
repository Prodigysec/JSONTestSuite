#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build"
archive="$build_dir/libfyaml-0.9.6.tar.gz"
checksum=a59cc3331e2eb903ec36933ad52a45888041cac31e44f553a00511131242c483
mkdir -p "$build_dir"
if [ ! -f "$archive" ]; then
    curl --fail --silent --show-error --location \
        'https://github.com/pantoniou/libfyaml/releases/download/v0.9.6/libfyaml-0.9.6.tar.gz' \
        -o "$archive.tmp"
    printf '%s  %s\n' "$checksum" "$archive.tmp" | sha256sum -c -
    mv "$archive.tmp" "$archive"
fi
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xzf "$archive" -C "$build_dir"
cd "$build_dir/libfyaml-0.9.6"
./configure
"${MAKE:-make}" -j2
printf 'Built %s\n' "$PWD/src/fy-tool"
