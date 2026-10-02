#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build"
mkdir -p "$build_dir/classes"
jar="$build_dir/fastjson2-2.0.53.jar"
checksum=ad1085113d3c42a45194baab44b5d0e1c4028e7422a4d39a6084133d58dfd877
if [ ! -f "$jar" ]; then
    curl --fail --silent --show-error --location \
        'https://repo.maven.apache.org/maven2/com/alibaba/fastjson2/fastjson2/2.0.53/fastjson2-2.0.53.jar' \
        -o "$jar.tmp"
    printf '%s  %s\n' "$checksum" "$jar.tmp" | sha256sum -c -
    mv "$jar.tmp" "$jar"
fi
printf '%s  %s\n' "$checksum" "$jar" | sha256sum -c -
"${JAVAC:-javac}" -encoding UTF-8 -cp "$jar" -d "$build_dir/classes" "$base_dir/TestJSONParsing.java"
printf 'Built %s\n' "$build_dir/classes/TestJSONParsing.class"
