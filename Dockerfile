# syntax=docker/dockerfile:1.7
FROM rust:1.78-slim-bookworm AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends pkg-config libssl-dev build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Prime the dependency cache.
COPY Cargo.toml Cargo.lock* rust-toolchain.toml ./
COPY programs/geas/Cargo.toml programs/geas/
COPY cli/Cargo.toml cli/
RUN mkdir -p programs/geas/src cli/src \
 && echo "fn main() {}" > cli/src/main.rs \
 && echo "" > programs/geas/src/lib.rs \
 && cargo build --release -p geas-cli || true

# Real sources.
COPY programs programs
COPY cli cli
COPY idl idl

RUN cargo build --release -p geas-cli

# Runtime image.
FROM debian:bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates libssl3 \
 && rm -rf /var/lib/apt/lists/* \
 && useradd -r -u 1001 -m geas

COPY --from=builder /app/target/release/geas-cli /usr/local/bin/geas

USER geas
ENTRYPOINT ["geas"]
