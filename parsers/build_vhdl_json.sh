#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build/vhdl-json"
revision=2ab1ebc2c788ececce152a49ffda706f84570e95
archive="$build_dir/source.tar.gz"
checksum=b78ad1422a2f4b5b8ee726563b224cb5db58976c660494a5fe3d3c93f9bc48a7
ghdl_cmd=$(command -v "${JSONTESTSUITE_GHDL:-ghdl}")
mkdir -p "$build_dir"
if [ ! -f "$archive" ]; then
    curl --fail --silent --show-error --location \
        "https://github.com/Paebbels/JSON-for-VHDL/archive/$revision.tar.gz" \
        -o "$archive.tmp"
    printf '%s  %s\n' "$checksum" "$archive.tmp" | sha256sum -c -
    mv "$archive.tmp" "$archive"
fi
printf '%s  %s\n' "$checksum" "$archive" | sha256sum -c -
tar -xzf "$archive" -C "$build_dir"
source_dir="$build_dir/JSON-for-VHDL-$revision/src"
cd "$build_dir"
"$ghdl_cmd" -a --std=08 "$source_dir/Encodings.pkg.vhdl"
"$ghdl_cmd" -a --std=08 "$source_dir/JSON.pkg.vhdl"
"$ghdl_cmd" -a --std=08 "$base_dir/test_vhdl_json.vhdl"
"$ghdl_cmd" -e --std=08 JSONSuiteVHDL
