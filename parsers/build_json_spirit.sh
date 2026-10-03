#!/bin/sh
set -eu

repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out="$repo/parsers/.build/json-spirit"
mkdir -p "$out"

source_archive="$out/json-spirit.tar.gz"
boost_archive="$out/boost-1.74.deb"
curl -LfsS https://codeload.github.com/cierelabs/json_spirit/tar.gz/c7245a39c94071804dcd1838d84415788c7f2c29 -o "$source_archive"
printf '%s  %s\n' 8ea54b9e75bece24ea776a28f292a0192fa73ced6bd48ce8e78931773c857f68 "$source_archive" | sha256sum -c -
curl -LfsS 'https://archive.ubuntu.com/ubuntu/pool/universe/b/boost1.74/libboost1.74-dev_1.74.0+ds1-23.1ubuntu3_amd64.deb' -o "$boost_archive"
printf '%s  %s\n' 97b0544205439a6073bf13e7df7b0f29d7363241115ee59011c0dcba2adb75b6 "$boost_archive" | sha256sum -c -

tar -xzf "$source_archive" -C "$out"
dpkg-deb -x "$boost_archive" "$out/boost"
source_dir="$out/json_spirit-c7245a39c94071804dcd1838d84415788c7f2c29"
"${CXX:-g++}" -std=c++17 -O2 -w -I"$source_dir" -I"$out/boost/usr/include" \
    "$repo/parsers/test_json_spirit.cpp" \
    "$source_dir/libs/json/src/io.cpp" "$source_dir/libs/json/src/value.cpp" \
    -o "$out/test_json_spirit"
