#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
build_dir="$base_dir/.build"
mkdir -p "$build_dir"
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
base_url=https://repo.maven.apache.org/maven2/org/clojure
fetch "$base_url/clojure/1.10.1/clojure-1.10.1.jar" "$build_dir/clojure-1.10.1.jar" \
    d4f6f991fd9ed2a59e7ea4779010b3b069a2b905f3463136c42201106b4ad21a
fetch "$base_url/spec.alpha/0.2.176/spec.alpha-0.2.176.jar" "$build_dir/spec.alpha-0.2.176.jar" \
    fc4e96ecff34ddd2ab7fd050e74ae1379342ee09daa6028da52024c5de836cc4
fetch "$base_url/core.specs.alpha/0.2.44/core.specs.alpha-0.2.44.jar" "$build_dir/core.specs.alpha-0.2.44.jar" \
    3b1ec4d6f0e8e41bf76842709083beb3b56adf3c82f9a4f174c3da74774b381c
fetch "$base_url/data.json/1.0.0/data.json-1.0.0.jar" "$build_dir/data.json-1.0.0.jar" \
    1b5f4f9ebefdc88a63e34dc2386ea18ea23f61439b53efefb0d9510661fb475d
fetch "$base_url/data.json/2.2.0/data.json-2.2.0.jar" "$build_dir/data.json-2.2.0.jar" \
    e8c23b3cce68d856ae2f71983fd12dd31a498795648289175a310ae070864e1e
for version in 1.0.0 2.2.0; do
    classes="$build_dir/classes/$version"
    mkdir -p "$classes"
    "${JAVAC:-javac}" --release 8 -d "$classes" "$base_dir/src/jsonsuite/EofPushbackReader.java"
    classpath="$classes:$base_dir/src:$build_dir/clojure-1.10.1.jar:$build_dir/spec.alpha-0.2.176.jar:$build_dir/core.specs.alpha-0.2.44.jar:$build_dir/data.json-$version.jar"
    "${JAVA:-java}" -cp "$classpath" clojure.main -e \
        "(binding [*compile-path* \"$classes\"] (compile 'jsonsuite.adapter))"
done
printf 'Prepared Clojure 1.10.1 and data.json 1.0.0 / 2.2.0 in %s\n' "$build_dir"
