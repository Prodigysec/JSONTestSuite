#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$#" -ne 2 ]; then
    printf 'Usage: run.sh 1.0.0|2.2.0 FILE\n' >&2
    exit 2
fi
case "$1" in
    1.0.0|2.2.0) ;;
    *) printf 'Unknown data.json version: %s\n' "$1" >&2; exit 2 ;;
esac
version=$1
shift
build_dir="$base_dir/.build"
for required in "$build_dir/classes/$version/jsonsuite/adapter__init.class" \
    "$build_dir/classes/$version/jsonsuite/EofPushbackReader.class" \
    "$build_dir/clojure-1.10.1.jar" "$build_dir/spec.alpha-0.2.176.jar" \
    "$build_dir/core.specs.alpha-0.2.44.jar" "$build_dir/data.json-$version.jar"; do
    if [ ! -f "$required" ]; then
        printf 'Missing build dependency: %s\n' "$required" >&2
        exit 2
    fi
done
classpath="$build_dir/classes/$version:$build_dir/clojure-1.10.1.jar:$build_dir/spec.alpha-0.2.176.jar:$build_dir/core.specs.alpha-0.2.44.jar:$build_dir/data.json-$version.jar"
exec "${JAVA:-java}" -cp "$classpath" clojure.main -m jsonsuite.adapter "$version" "$1"
