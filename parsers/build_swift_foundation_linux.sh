#!/bin/sh
set -eu
base_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
image='swift@sha256:19792fa7ef68fb0e0ca5763ec3dfd40d6461afca7c081eb689e2e374fa80c0be'
mkdir -p "$base_dir/.build/swift-foundation-linux"
docker image inspect "$image" >/dev/null 2>&1 || docker pull "$image"
docker run --rm --network none --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$base_dir,dst=$base_dir" \
    --workdir "$base_dir" --env HOME=/tmp \
    "$image" swiftc -O "$base_dir/test_swift_foundation_linux.swift" \
    -o "$base_dir/.build/swift-foundation-linux/test_swift_foundation_linux"
