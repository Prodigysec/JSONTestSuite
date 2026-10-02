#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build"
revision=921f3e3314edcd12eb9484435d651974454ce456
mkdir -p "$build_dir/classes"
fetch() {
    url=$1
    output=$2
    checksum=$3
    if [ ! -f "$output" ]; then
        curl --fail --silent --show-error --location "$url" -o "$output.tmp"
        printf '%s  %s\n' "$checksum" "$output.tmp" | sha256sum -c -
        mv "$output.tmp" "$output"
    fi
    printf '%s  %s\n' "$checksum" "$output" | sha256sum -c -
}
fetch "https://codeload.github.com/realtimetech-solution/opack/tar.gz/$revision" \
    "$build_dir/opack.tar.gz" \
    41f41b9dba7a88067a27a46019dddbdcbc740a019114c029ebe86956acc8307d
fetch 'https://repo.maven.apache.org/maven2/org/jetbrains/annotations/24.1.0/annotations-24.1.0.jar' \
    "$build_dir/annotations-24.1.0.jar" \
    27a770dc7ce50500918bb8c3c0660c98290630ec796b5e3cf6b90f403b3033c6
tar -xzf "$build_dir/opack.tar.gz" -C "$build_dir"
# Relative paths in the argument file also work when the checkout contains spaces.
cd "$build_dir"
find "opack-$revision/src/main/java" -name '*.java' -print | sort > sources.txt
"${JAVAC:-javac}" -encoding UTF-8 -cp annotations-24.1.0.jar \
    -d classes @sources.txt "$base_dir/TestJSONParsing.java"
printf 'Built %s\n' "$build_dir/classes/TestJSONParsing.class"
