#!/bin/sh
set -eu

repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
image=rust@sha256:3914072ca0c3b8aad871db9169a651ccfce30cf58303e5d6f2db16d1d8a7e58f

docker run --rm --pull never \
    --user "$(id -u):$(id -g)" \
    --mount "type=bind,src=$repo,dst=/work" \
    -w /work/parsers/test_json-rust-serde_json/rj \
    -e CARGO_HOME=/work/parsers/.build/rust-serde-json/cargo-home \
    -e CARGO_TARGET_DIR=/work/parsers/.build/rust-serde-json \
    "$image" cargo build --locked
