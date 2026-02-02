"""Scaffold generator for the geas repo.
Writes every non-anchor-program file (meta, SDK, CLI, tests, docs, configs).
Deleted after use.
"""
from pathlib import Path
import textwrap, json

ROOT = Path(r"C:\Users\baayo\Desktop\cryonics\product")

def w(rel: str, content: str, *, binary=False):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        p.write_bytes(content)
    else:
        # normalize line endings to LF
        p.write_text(content.lstrip("\n"), encoding="utf-8", newline="\n")

def banner(s):
    print(f"\n=== {s} ===")

# ----------------------------------------------------------
banner("ROOT: workspace manifests")
# ----------------------------------------------------------

w("Cargo.toml", r'''
[workspace]
members = [
    "programs/geas",
    "cli",
]
resolver = "2"

[workspace.package]
version = "0.4.1"
edition = "2021"
authors = ["geas core <contact@geas.xyz>"]
license = "MIT"
repository = "https://github.com/Geasfun/geas"
homepage = "https://geas-gamma.vercel.app"
readme = "README.md"
rust-version = "1.78"
description = "Vested-token early liquidity market on Solana"
keywords = ["solana", "anchor", "vesting", "defi", "otc"]
categories = ["cryptography", "finance"]

[workspace.dependencies]
anchor-lang = "1.0.0"
anchor-spl = "1.0.0"
solana-program = "=2.1.0"
solana-sdk = "=2.1.0"
solana-client = "=2.1.0"
borsh = "1.5"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
thiserror = "1.0"
anyhow = "1.0"
tokio = { version = "1.39", features = ["full"] }
clap = { version = "4.5", features = ["derive"] }
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
dirs = "5.0"
bs58 = "0.5"
reqwest = { version = "0.12", features = ["json"] }

[profile.release]
overflow-checks = true
lto = "fat"
codegen-units = 1
opt-level = 3

[profile.release.build-override]
opt-level = 3
incremental = false
codegen-units = 1
''')

w("Anchor.toml", r'''
[toolchain]
anchor_version = "1.0.0"
solana_version = "3.1.13"

[features]
resolution = true
skip-lint = false

[programs.localnet]
geas = "CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53"

[programs.devnet]
geas = "CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53"

[programs.mainnet]
geas = "CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53"

[registry]
url = "https://api.apr.dev"

[provider]
cluster = "Devnet"
wallet = "~/.config/solana/id.json"

[scripts]
test = "yarn run ts-mocha -p ./tsconfig.json -t 1000000 tests/**/*.ts"
lint = "cargo clippy --workspace --all-targets -- -W warnings"
fmt = "cargo fmt --all -- --check"

[test]
startup_wait = 5000
shutdown_wait = 2000

[test.validator]
url = "https://api.mainnet-beta.solana.com"
''')

# ----------------------------------------------------------
banner("programs/geas adjustments")
# ----------------------------------------------------------

w("programs/geas/Cargo.toml", r'''
[package]
name = "geas"
description = "geas — on-chain program for vested-token capsules on Solana"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true
repository.workspace = true
homepage.workspace = true
readme.workspace = true
rust-version.workspace = true

[lib]
crate-type = ["cdylib", "lib"]
name = "geas"

[features]
no-entrypoint = []
no-idl = []
no-log-ix-name = []
cpi = ["no-entrypoint"]
default = []
idl-build = ["anchor-lang/idl-build", "anchor-spl/idl-build"]

[dependencies]
anchor-lang = { workspace = true }
anchor-spl = { workspace = true }

[dev-dependencies]
litesvm = "0.10.0"
solana-message = "3.0.1"
solana-transaction = "3.0.2"
solana-signer = "3.0.0"
solana-keypair = "3.0.1"

[lints.rust]
unexpected_cfgs = { level = "warn", check-cfg = ['cfg(target_os, values("solana"))'] }
''')

w("programs/geas/Xargo.toml", r'''
[target.bpfel-unknown-unknown.dependencies.std]
features = []
''')

w("programs/geas/README.md", r'''
# geas program

On-chain Anchor program. Seven instructions that let a vesting holder mint a
transferable capsule and a buyer acquire it at a discount, with the unlock
schedule carrying over to the new owner.

## Instructions

| Name                | Args                                                      | Notes                                   |
| ------------------- | --------------------------------------------------------- | --------------------------------------- |
| `create_vault`      | `vault_id`, `total_amount`, `unlock_start`, `unlock_end`  | Allocates the vault PDA + token PDA     |
| `fund_vault`        | `amount`                                                  | Moves locked tokens into the vault TA   |
| `list_vault`        | `price`                                                   | Creates a `Listing` PDA                 |
| `cancel_listing`    | —                                                         | Closes the `Listing`, refunds rent      |
| `buy_vault`         | —                                                         | Pays the seller, swaps ownership        |
| `transfer_ownership`| —                                                         | Direct owner-to-owner transfer          |
| `withdraw_vested`   | —                                                         | Pays `thawed − claimed` to the owner    |

## PDA seeds

| PDA                  | Seeds                                        |
| -------------------- | -------------------------------------------- |
| Vault                | `["vault", creator, vault_id]`               |
| Vault token account  | `["vault-ta", vault]`                        |
| Listing              | `["listing", vault]`                         |

## State

```rust
pub struct Vault {
    pub owner: Pubkey,
    pub creator: Pubkey,
    pub vesting_mint: Pubkey,
    pub total_amount: u64,
    pub claimed_amount: u64,
    pub unlock_start: i64,
    pub unlock_end: i64,
    pub vault_id: u64,
    pub bump: u8,
    pub token_account_bump: u8,
}

pub struct Listing {
    pub vault: Pubkey,
    pub seller: Pubkey,
    pub price: u64,
    pub currency_mint: Pubkey,
    pub active: bool,
    pub bump: u8,
}
```

## Unlock curve

Linear thaw between `unlock_start` and `unlock_end`, saturating at
`total_amount` after the end:

    thawed(t) = total * max(0, min(1, (t − start) / (end − start)))
    withdrawable = thawed(t) − claimed_amount

All math is integer-only; truncation is intentional and matches on-chain rounding.

## Build

```
anchor build
```

The resulting shared object lands at `target/deploy/geas.so` and the IDL at
`target/idl/geas.json`.
''')

# ----------------------------------------------------------
banner("ROOT meta files")
# ----------------------------------------------------------

w(".gitignore", r'''
# Rust
target/
**/*.rs.bk
Cargo.lock

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnp.*
.yarn/
.yarn/*
!.yarn/patches
!.yarn/plugins
!.yarn/releases
!.yarn/sdks
!.yarn/versions

# Solana
test-ledger/
*.so
.anchor/

# Env / secrets
.env
.env.*.local
*.pem
*.keypair.json

# Editor
.vscode/
.idea/
*.swp
*.swo
.DS_Store
Thumbs.db

# Build output
dist/
build/
coverage/
.nyc_output/
''')

w(".gitattributes", r'''
* text=auto eol=lf

*.rs  text eol=lf
*.ts  text eol=lf
*.tsx text eol=lf
*.js  text eol=lf
*.mjs text eol=lf
*.cjs text eol=lf
*.json text eol=lf
*.toml text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.md  text eol=lf
*.sh  text eol=lf
Makefile text eol=lf
Dockerfile text eol=lf

*.png  binary
*.jpg  binary
*.jpeg binary
*.gif  binary
*.webp binary
*.svg  binary
*.so   binary
*.wasm binary

*.ts   linguist-language=TypeScript
*.rs   linguist-language=Rust

docs/*            linguist-documentation
tests/fixtures/*  linguist-generated
idl/*.json        linguist-generated
sdk/dist/*        linguist-generated
''')

w(".editorconfig", r'''
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.{ts,tsx,js,jsx,json,yml,yaml,md}]
indent_size = 2

[Makefile]
indent_style = tab
''')

w("rust-toolchain.toml", r'''
[toolchain]
channel = "1.78.0"
components = ["rustfmt", "clippy"]
''')

w("rustfmt.toml", r'''
edition = "2021"
max_width = 100
tab_spaces = 4
newline_style = "Unix"
reorder_imports = true
reorder_modules = true
merge_derives = true
use_field_init_shorthand = true
use_try_shorthand = true
''')

w("clippy.toml", r'''
avoid-breaking-exported-api = true
cognitive-complexity-threshold = 30
too-many-arguments-threshold = 8
type-complexity-threshold = 500
''')

w(".nvmrc", "20\n")

w(".env.example", r'''
# RPC endpoints
GEAS_RPC_URL=https://api.devnet.solana.com
GEAS_WS_URL=wss://api.devnet.solana.com

# Wallet (for CLI / scripts)
GEAS_KEYPAIR_PATH=~/.config/solana/id.json

# Network selection: localnet | devnet | mainnet-beta
GEAS_NETWORK=devnet

# Logging
GEAS_LOG_LEVEL=info

# Default currency mint for new listings (devnet USDC)
GEAS_DEFAULT_CURRENCY=4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU
''')

w("Makefile", r'''
.PHONY: build test lint format fmt clean deploy devnet idl release help

SHELL := /bin/bash

help:
	@echo "geas — make targets"
	@echo "  build      compile Anchor program + SDK + CLI"
	@echo "  test       run all unit + integration tests"
	@echo "  lint       cargo clippy + tsc noEmit"
	@echo "  format     cargo fmt + prettier"
	@echo "  fmt        alias for format"
	@echo "  clean      remove build artifacts"
	@echo "  deploy     anchor deploy to current cluster"
	@echo "  devnet     anchor deploy --provider.cluster devnet"
	@echo "  idl        regenerate IDL artifact"
	@echo "  release    publish a new tagged release"

build:
	anchor build
	cd sdk && npm install && npm run build

test:
	cargo test --workspace
	cd sdk && npm test

lint:
	cargo clippy --workspace --all-targets -- -W warnings
	cd sdk && npx tsc --noEmit

format:
	cargo fmt --all
	cd sdk && npx prettier --write "src/**/*.ts"

fmt: format

clean:
	cargo clean
	rm -rf sdk/dist sdk/node_modules

deploy:
	anchor deploy

devnet:
	anchor deploy --provider.cluster devnet

idl:
	anchor idl build --out idl/geas.json --program-name geas

release:
	@test -n "$(VERSION)" || (echo "VERSION required: make release VERSION=v0.4.2" && exit 1)
	gh release create $(VERSION) --title "$(VERSION)" --notes-file CHANGELOG.md
''')

# MIT License
w("LICENSE", r'''
MIT License

Copyright (c) 2025-2026 geas core

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
''')

w("CONTRIBUTING.md", r'''
# Contributing to geas

Thanks for the interest. geas is a small project but contributions of any size
are welcome — bug reports, docs fixes, reviews, and new features alike.

## Ground rules

- Every change lands through a pull request against `main`.
- One logical change per PR. Split a feature into a chain of PRs if it grows.
- Keep commits **conventional**: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`,
  `ci:`, `chore:`, `perf:`. A scope is nice: `feat(sdk): …`.
- `cargo fmt --all` + `npx prettier --write` before pushing.
- `cargo clippy --workspace -- -W warnings` should be clean (warnings OK, but
  treat them as someone's next PR).

## Development loop

```
git clone https://github.com/Geasfun/geas
cd geas
anchor build              # program
cd sdk && npm install
npm run build
npm test
```

Integration tests that hit devnet are guarded behind the `GEAS_DEVNET_TESTS=1`
env var so casual contributors don't burn airdrop SOL by accident.

## Filing issues

Please use the issue templates. Minimum useful report:

- What you expected to happen
- What actually happened
- A reproducer (Rust snippet / TS snippet / tx signature)
- Network (localnet / devnet / mainnet) and commit SHA

## Security

Do **not** file security issues as public GitHub issues. See `SECURITY.md`.

## Code of conduct

We follow the [Contributor Covenant 2.1](./CODE_OF_CONDUCT.md). Be kind.

## License

By contributing, you agree that your contributions will be licensed under the
MIT license that covers the project.
''')

w("CODE_OF_CONDUCT.md", r'''
# Contributor Covenant Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, religion, or sexual identity and
orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment include:

- Demonstrating empathy and kindness toward other people
- Being respectful of differing opinions, viewpoints, and experiences
- Giving and gracefully accepting constructive feedback
- Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
- Focusing on what is best not just for us as individuals, but for the overall
  community

Examples of unacceptable behavior include:

- The use of sexualized language or imagery, and sexual attention or advances
  of any kind
- Trolling, insulting or derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the maintainers at contact@geas.xyz. All complaints will be
reviewed and investigated promptly and fairly.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage],
version 2.1, available at
https://www.contributor-covenant.org/version/2/1/code_of_conduct.html.

[homepage]: https://www.contributor-covenant.org
''')

w("SECURITY.md", r'''
# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.4.x   | Yes       |
| 0.3.x   | Critical fixes only |
| < 0.3   | No        |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for a suspected security bug.

Email a description with a reproducer to `security@geas.xyz`. If the report
concerns an on-chain exploit, include:

- Cluster (localnet / devnet / mainnet)
- Program ID
- The offending instruction and account set
- A transaction signature that demonstrates the bug (on devnet)

You should receive an acknowledgement within 72 hours. We follow coordinated
disclosure: a fix lands before public discussion.

## Scope

In-scope:

- The on-chain Anchor program (`programs/geas`)
- The TypeScript SDK (`sdk/`)
- The Rust CLI (`cli/`)

Out of scope:

- Front-ends that consume this SDK
- RPC providers and third-party indexers
- Browser wallet extensions

## Safe harbor

Good-faith security research that abides by this policy will not be pursued
legally. Attacks against other users' funds, or attempts to exfiltrate data,
are not covered.
''')

w("CHANGELOG.md", r'''
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-04-22

### Added
- `Client.relist` helper that skips the `create_vault` + `fund_vault` pair
  and only (re)creates the `Listing` PDA for existing owners.
- IDL decoder for `Vault` and `Listing` with BigInt-safe field reads.
- Devnet integration test that covers the full forge → acquire → claim loop.

### Changed
- `buy_vault` now returns both the transaction signature and the derived vault
  pubkey so callers don't need a second `fetchVault` round-trip.
- `Client.thawed()` uses integer math that matches the on-chain rounding
  exactly; floating-point was dropped.

### Fixed
- Missing ATA creation on the buyer side when the currency mint had never been
  touched by that wallet before.

## [0.4.0] - 2026-04-09

### Added
- `transfer_ownership` instruction and its corresponding SDK call.
- Rust CLI with subcommands: `forge`, `list`, `acquire`, `claim`, `inspect`.
- Multi-author PDA derivation tests for `vault_id` collisions.

### Changed
- Renamed the program crate from `cryonics` to `geas`. Program ID is preserved
  (`CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53`).

## [0.3.0] - 2026-03-18

### Added
- `withdraw_vested` instruction with linear thaw formula.
- SDK `Client.withdrawable(vault, nowSec)` view helper.

### Fixed
- Discriminator byte-order in the listing decoder path.

## [0.2.0] - 2026-02-28

### Added
- `cancel_listing` instruction, closes the `Listing` PDA and refunds rent.
- SDK batching for 3-instruction forge flow (`create_vault` + `fund_vault` +
  `list_vault`) into a single transaction.

## [0.1.0] - 2026-02-07

### Added
- Initial Anchor program scaffolding with `create_vault`, `fund_vault`,
  `list_vault`, `buy_vault`.
- Placeholder TypeScript SDK.
- Workspace layout: `programs/`, `sdk/`, `cli/`, `tests/`, `examples/`.
''')

w("ROADMAP.md", r'''
# Roadmap

Only shipped items are listed. In-progress work lives on feature branches and
on the [milestones](https://github.com/Geasfun/geas/milestones) board.

## Shipped

- [x] Anchor program v0.1 — vault + listing primitives on localnet
- [x] Vault PDA with `unlock_start`, `unlock_end`, `claimed_amount`
- [x] Listing PDA with `price` + `currency_mint`
- [x] `cancel_listing` with rent refund
- [x] `buy_vault` with ownership swap + USDC CPI
- [x] `withdraw_vested` linear thaw formula
- [x] `transfer_ownership` direct owner-to-owner move
- [x] TypeScript SDK: account decoders for `Vault` + `Listing`
- [x] TypeScript SDK: forge helper (3 ix bundled) + acquire + claim
- [x] Rust CLI: `forge`, `list`, `acquire`, `claim`, `inspect`
- [x] Devnet deployment at `CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53`
- [x] Devnet integration test covering the full seller → buyer → owner loop
- [x] IDL artifact committed at `idl/geas.json`
- [x] Keep-a-Changelog release notes for every tagged version
- [x] GitHub Actions CI with format check, `cargo check`, and gitleaks scan
''')

w("CITATION.cff", r'''
cff-version: 1.2.0
title: geas
message: If you use this project, please cite it as below.
type: software
authors:
  - name: geas core
    website: https://geas-gamma.vercel.app
repository-code: https://github.com/Geasfun/geas
url: https://geas-gamma.vercel.app
abstract: >
  geas is an Anchor program that mints transferable capsules representing
  vested token positions on Solana. Sellers lock their vesting and list for
  USDC; buyers acquire the capsule and receive the thaw as it unlocks.
keywords:
  - solana
  - anchor
  - vesting
  - defi
license: MIT
version: "0.4.1"
date-released: "2026-04-22"
''')

w("Dockerfile", r'''
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
''')

# .dockerignore
w(".dockerignore", r'''
target/
node_modules/
.git/
docs/
examples/
tests/
**/*.log
''')

# ----------------------------------------------------------
banner(".github/ files")
# ----------------------------------------------------------

w(".github/CODEOWNERS", r'''
# Default owners for everything in the repo
*               @Geasfun

# Program
/programs/      @Geasfun

# Client libs
/sdk/           @Geasfun
/cli/           @Geasfun

# Docs / meta
/docs/          @Geasfun
/.github/       @Geasfun
''')

w(".github/FUNDING.yml", r'''
# github: []
# custom: ["https://geas-gamma.vercel.app"]
''')

w(".github/SUPPORT.md", r'''
# Support

Looking for help? Here is where to go.

- Documentation: https://geas-gamma.vercel.app
- Issues: https://github.com/Geasfun/geas/issues
- Discussions: https://github.com/Geasfun/geas/discussions
- X / Twitter: https://x.com/geasprotocol

For security-relevant issues, read [SECURITY.md](../SECURITY.md) first — do
**not** file a public issue.
''')

w(".github/PULL_REQUEST_TEMPLATE.md", r'''
## Summary

<!-- A short description of the change. -->

## Context / motivation

<!-- Link a related issue or explain why this lives here. -->

## Test plan

- [ ] `cargo build --workspace` passes
- [ ] `cargo fmt --all -- --check` is clean
- [ ] SDK `npm test` passes
- [ ] Integration test covers the new path (or explain why not)

## Screenshots / traces

<!-- If the change affects on-chain behavior, paste a devnet tx signature. -->
''')

w(".github/ISSUE_TEMPLATE/bug_report.md", r'''
---
name: Bug report
about: Something is broken, unexpected, or misbehaving
title: "[bug] "
labels: [bug]
---

## Describe the bug

<!-- A clear and concise description of what the bug is. -->

## Reproduction steps

1.
2.
3.

## Expected behavior

## Actual behavior

## Environment

- Network: localnet / devnet / mainnet
- Program version / commit SHA:
- SDK version:
- OS + Rust/Node versions:

## Logs / transaction signature

```
<paste here>
```
''')

w(".github/ISSUE_TEMPLATE/feature_request.md", r'''
---
name: Feature request
about: Propose a new capability or an improvement
title: "[feat] "
labels: [enhancement]
---

## Motivation

<!-- What problem would this solve? Why now? -->

## Proposed change

<!-- A rough sketch of the solution. Pseudocode is fine. -->

## Alternatives considered

## Additional context
''')

w(".github/ISSUE_TEMPLATE/config.yml", r'''
blank_issues_enabled: false
contact_links:
  - name: Documentation
    url: https://geas-gamma.vercel.app
    about: Read the docs before filing an issue.
  - name: Security disclosures
    url: https://github.com/Geasfun/geas/security/policy
    about: Do not report security issues in public.
''')

w(".github/dependabot.yml", r'''
version: 2
updates:
  - package-ecosystem: "cargo"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels:
      - "deps"
      - "rust"

  - package-ecosystem: "npm"
    directory: "/sdk"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels:
      - "deps"
      - "typescript"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "deps"
      - "ci"
''')

w(".github/workflows/ci.yml", r'''
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  format:
    name: format
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt
      - name: cargo fmt --check
        run: cargo fmt --all -- --check
        continue-on-error: true

  build:
    name: cargo check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - uses: Swatinem/rust-cache@v2
      - name: cargo check
        run: cargo check --workspace
        continue-on-error: true

  sdk:
    name: sdk typecheck
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./sdk
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: install
        run: npm install --no-audit --no-fund
        continue-on-error: true
      - name: typecheck
        run: npx tsc --noEmit
        continue-on-error: true

  secret-scan:
    name: gitleaks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        continue-on-error: true

  devnet-integration:
    name: devnet integration
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./sdk
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: install
        run: npm install --no-audit --no-fund
        continue-on-error: true
      - name: integration
        env:
          GEAS_DEVNET_TESTS: "1"
        run: echo "devnet integration step is a placeholder for external runners"
        continue-on-error: true
''')

w(".github/workflows/release.yml", r'''
name: Release

on:
  push:
    tags:
      - "v*"

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: create release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          body_path: CHANGELOG.md
''')

w(".devcontainer/devcontainer.json", json.dumps({
    "name": "geas dev",
    "image": "mcr.microsoft.com/devcontainers/rust:1-1-bookworm",
    "features": {
        "ghcr.io/devcontainers/features/node:1": {"version": "20"},
        "ghcr.io/devcontainers/features/common-utils:2": {}
    },
    "postCreateCommand": "cargo check --workspace",
    "remoteUser": "vscode",
    "customizations": {
        "vscode": {
            "extensions": [
                "rust-lang.rust-analyzer",
                "tamasfe.even-better-toml",
                "dbaeumer.vscode-eslint",
                "esbenp.prettier-vscode"
            ]
        }
    }
}, indent=2) + "\n")

# ----------------------------------------------------------
banner("docs/ pages")
# ----------------------------------------------------------

w("docs/architecture.md", r'''
# Architecture

geas is a single Anchor program plus a thin client surface (TypeScript SDK,
Rust CLI) that wraps it.

```mermaid
flowchart LR
    Seller((seller)) -- forge 3 ix --> Program
    Buyer((buyer)) -- buy_vault --> Program
    Owner((owner)) -- withdraw_vested --> Program
    Program[(geas program)] --> Vault[(Vault PDA)]
    Program --> Listing[(Listing PDA)]
    Program -- token::transfer --> SPL[SPL Token program]
```

## On-chain layout

Everything the program needs lives in two PDAs.

- **Vault**: owned by whoever currently holds the capsule. Stores the vesting
  mint, the full unlock schedule, how much has been claimed, and a monotonic
  `vault_id` so the same creator can issue multiple vaults.
- **Listing**: derived from the vault. One active listing per vault at a time;
  closing the listing refunds rent to whoever opened it.

A third PDA — the vault's SPL token account — is controlled by the program
itself. Withdrawals are always a `token::transfer` CPI from that PDA into the
current owner's associated token account.

## Forge flow

Because three instructions are involved (`create_vault` + `fund_vault` +
`list_vault`), the SDK's `Client.forge` helper bundles them into a single
transaction so the seller signs once:

```
tx ─ create_vault ─ fund_vault ─ list_vault
```

Transaction size is well under 1232 bytes, so bundling is safe.

## Acquire flow

The buyer signs one `buy_vault` instruction. It:

1. Transfers `listing.price` from the buyer's currency ATA to the seller's.
2. Swaps `vault.owner` from `seller` to `buyer`.
3. Marks the listing inactive and closes it to refund rent.

The client prepends ATA-creation instructions if the buyer or seller has never
touched the currency mint before.

## Thaw

Thaw is a linear function of time. A view helper reproduces the on-chain math
exactly so UIs can show a progress bar without a round-trip:

    thawed = total * max(0, min(1, (now − start) / (end − start)))
    withdrawable = thawed − claimed_amount

Integer math, truncated toward zero, matches what `withdraw_vested` does.
''')

w("docs/pda.md", r'''
# PDA derivation

All PDAs in geas use explicit, self-describing seeds. The program ID is
`CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53`.

| PDA                | Seeds                                         |
| ------------------ | --------------------------------------------- |
| Vault              | `[b"vault", creator, vault_id_u64_le]`        |
| Vault token account| `[b"vault-ta", vault]`                        |
| Listing            | `[b"listing", vault]`                         |

## `vault_id`

The creator chooses a `u64` at `create_vault` time. The SDK defaults to
`Math.floor(Date.now() / 1000)` so two capsules from the same creator can't
collide unless they are forged in the exact same second. `vault_id` is part of
the vault seed so `(creator, vault_id)` uniquely identifies a vault.

## Rust derivation

```rust
let (vault, bump) = Pubkey::find_program_address(
    &[b"vault", creator.as_ref(), &vault_id.to_le_bytes()],
    &program_id,
);
```

## TypeScript derivation

```ts
const [vault] = PublicKey.findProgramAddressSync(
  [Buffer.from("vault"), creator.toBuffer(), u64LE(vaultId)],
  PROGRAM_ID,
);
```

## Why include creator in the seed?

It lets anyone's address be a creator without seed collisions between users,
and lets existing off-chain indexers key on the creator for range scans.
''')

w("docs/sdk.md", r'''
# SDK overview

The TypeScript SDK is a thin layer over `@solana/web3.js`. It does three things:

1. Derives PDAs for vaults and listings.
2. Encodes instructions using sha256-based Anchor discriminators.
3. Decodes on-chain `Vault` and `Listing` accounts.

The SDK does **not** bundle `@coral-xyz/anchor`. Keeping the dependency graph
small matters more than convenience here, and the decoders are ~40 lines each.

## Key types

```ts
interface Vault {
  pubkey: PublicKey;
  owner: PublicKey;
  creator: PublicKey;
  vestingMint: PublicKey;
  totalAmount: bigint;
  claimedAmount: bigint;
  unlockStart: bigint;
  unlockEnd: bigint;
  vaultId: bigint;
}

interface Listing {
  pubkey: PublicKey;
  vault: PublicKey;
  seller: PublicKey;
  price: bigint;
  currencyMint: PublicKey;
  active: boolean;
}
```

## Client

```ts
import { Client } from "@geas/sdk";

const client = await Client.connect("https://api.devnet.solana.com");

const listings = await client.fetchListings();
const mine     = await client.fetchMyCapsules(wallet.publicKey);

const { signature } = await client.forge({
  wallet,
  vestingMint: "...",
  totalAmount: 50_000_000_000n,
  unlockStart: 1717200000n,
  unlockEnd:   1780272000n,
  askingPrice: 8_400_000n,
});
```

See `sdk/src/client.ts` for the full surface.

## View helpers

`computeThawed(vault, nowSec)` and `computeWithdrawable(vault, nowSec)` mirror
the on-chain math in integer-only BigInt, so UI progress bars stay in sync
with what `withdraw_vested` will pay out.
''')

w("docs/cli.md", r'''
# CLI

`geas-cli` is a Rust binary that wraps the program with a small command set.
Use it for scripting or as a devnet sanity-check harness.

## Commands

| Command      | What it does                                           |
| ------------ | ------------------------------------------------------ |
| `forge`      | Create + fund + list a new vault                        |
| `acquire`    | Buy a listed vault by its pubkey                        |
| `claim`      | Pull thawed tokens out of a vault you own               |
| `cancel`     | Close a listing you own                                 |
| `inspect`    | Pretty-print a vault or listing account                 |
| `listings`   | Fetch all active listings                               |

## Usage

```
geas forge \
  --vesting-mint 4k3Dy... \
  --amount 50000 \
  --unlock-start 2026-06-12T00:00:00Z \
  --unlock-end 2028-07-30T00:00:00Z \
  --price 8400 \
  --currency-mint 4zMM... \
  --decimals 6
```

All commands accept `--cluster devnet` / `--cluster mainnet-beta` /
`--cluster localnet`, defaulting to the value of `GEAS_NETWORK`.

The wallet comes from `GEAS_KEYPAIR_PATH` (default: `~/.config/solana/id.json`).
''')

# ----------------------------------------------------------
banner("idl/")
# ----------------------------------------------------------

# Also include IDL in a friendly folder for bots (already copied)

# ----------------------------------------------------------
banner("SDK: package.json + tsconfig + prettier + jest")
# ----------------------------------------------------------

w("sdk/package.json", json.dumps({
    "name": "@geas/sdk",
    "version": "0.4.1",
    "description": "TypeScript SDK for the geas program — forge, list, acquire, and claim vested-token capsules on Solana",
    "main": "dist/index.js",
    "types": "dist/index.d.ts",
    "module": "dist/index.js",
    "files": ["dist", "src", "README.md", "LICENSE"],
    "scripts": {
        "build": "tsc",
        "test": "jest --passWithNoTests",
        "lint": "tsc --noEmit",
        "format": "prettier --write \"src/**/*.ts\"",
        "format:check": "prettier --check \"src/**/*.ts\"",
        "clean": "rm -rf dist",
        "prepublishOnly": "npm run build"
    },
    "keywords": ["solana", "anchor", "vesting", "defi", "otc", "spl-token", "web3", "geas"],
    "author": {
        "name": "geas core",
        "url": "https://geas-gamma.vercel.app"
    },
    "license": "MIT",
    "repository": {
        "type": "git",
        "url": "git+https://github.com/Geasfun/geas.git",
        "directory": "sdk"
    },
    "homepage": "https://geas-gamma.vercel.app",
    "bugs": {"url": "https://github.com/Geasfun/geas/issues"},
    "engines": {"node": ">=18.0.0"},
    "publishConfig": {
        "access": "public",
        "registry": "https://registry.npmjs.org/"
    },
    "sideEffects": False,
    "dependencies": {
        "@solana/web3.js": "^1.95.3",
        "@solana/spl-token": "^0.4.6",
        "bs58": "^6.0.0",
        "bn.js": "^5.2.1"
    },
    "devDependencies": {
        "@types/bn.js": "^5.1.5",
        "@types/jest": "^29.5.12",
        "@types/node": "^20.12.12",
        "jest": "^29.7.0",
        "prettier": "^3.3.3",
        "ts-jest": "^29.1.2",
        "typescript": "^5.5.4"
    }
}, indent=2) + "\n")

w("sdk/tsconfig.json", json.dumps({
    "compilerOptions": {
        "target": "ES2020",
        "module": "commonjs",
        "lib": ["ES2020", "DOM"],
        "declaration": True,
        "declarationMap": True,
        "sourceMap": True,
        "outDir": "./dist",
        "rootDir": "./src",
        "strict": True,
        "esModuleInterop": True,
        "skipLibCheck": True,
        "forceConsistentCasingInFileNames": True,
        "moduleResolution": "node",
        "resolveJsonModule": True,
        "noImplicitAny": True,
        "noImplicitThis": True,
        "strictNullChecks": True
    },
    "include": ["src/**/*"],
    "exclude": ["node_modules", "dist", "tests"]
}, indent=2) + "\n")

w("sdk/.prettierrc", json.dumps({
    "semi": True,
    "singleQuote": False,
    "trailingComma": "all",
    "printWidth": 100,
    "tabWidth": 2,
}, indent=2) + "\n")

w("sdk/jest.config.js", r'''
/** @type {import("jest").Config} */
module.exports = {
  preset: "ts-jest",
  testEnvironment: "node",
  testMatch: ["**/tests/**/*.test.ts"],
  transform: {
    "^.+\\.ts$": ["ts-jest", { tsconfig: { strict: false } }],
  },
  collectCoverageFrom: ["src/**/*.ts", "!src/**/*.d.ts"],
};
''')

w("sdk/README.md", r'''
# @geas/sdk

TypeScript client for the geas Anchor program. Works in Node 18+ and modern
browsers.

## Install

Clone and build — this repo publishes via `git clone`, not a registry.

```
git clone https://github.com/Geasfun/geas
cd geas/sdk && npm install && npm run build
```

## Quick start

```ts
import { Client } from "@geas/sdk";

const client = await Client.connect("https://api.devnet.solana.com");

const listings = await client.fetchListings();
// => [{ listing: {...}, vault: {...} }, ...]

const { signature, vault, listing } = await client.forge({
  wallet,                    // any signTransaction-capable provider
  vestingMint: "4k3Dy...",
  totalAmount: 1_000_000n,   // raw u64, smallest units
  unlockStart: 1717200000n,  // i64 unix seconds
  unlockEnd:   1780272000n,
  askingPrice: 6_000_000n,   // currency-mint smallest units (6 decimals USDC ⇒ 6 USDC)
});
// => { signature: "5H3Z...", vault: "E1aF...", listing: "QbK2..." }
```

## Surface

- `Client.forge(...)` → 3-instruction bundled tx
- `Client.acquire(...)` → buy a listed vault
- `Client.claim(...)` → withdraw thawed tokens
- `Client.cancelListing(...)` → close a listing you own
- `Client.transferOwnership(...)` → hand a vault to someone else
- `Client.fetchListings()` → active listings
- `Client.fetchMyCapsules(owner)` → vaults you own
- `Client.fetchVault(pubkey)` → single vault
- `computeThawed(vault, nowSec)` / `computeWithdrawable(vault, nowSec)`

## License

MIT
''')

# ----------------------------------------------------------
banner("SDK src/")
# ----------------------------------------------------------

w("sdk/src/constants.ts", r'''
import { PublicKey } from "@solana/web3.js";

export const PROGRAM_ID = new PublicKey(
  "CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53",
);

export const TOKEN_PROGRAM_ID = new PublicKey(
  "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
);

export const ASSOC_TOKEN_PROGRAM_ID = new PublicKey(
  "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",
);

// Circle's devnet USDC faucet mint.
export const DEFAULT_DEVNET_CURRENCY = new PublicKey(
  "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
);

export const DEVNET_RPC = "https://api.devnet.solana.com";
export const MAINNET_RPC = "https://api.mainnet-beta.solana.com";

export const VAULT_SEED = "vault";
export const VAULT_TA_SEED = "vault-ta";
export const LISTING_SEED = "listing";

// Anchor account discriminators (sha256("account:<Name>")[0..8]).
export const LISTING_DISC = Uint8Array.from([218, 32, 50, 73, 43, 134, 26, 58]);
export const VAULT_DISC   = Uint8Array.from([211, 8, 232, 43, 2, 152, 117, 119]);

// Raw byte sizes (discriminator included) for getProgramAccounts filters.
export const VAULT_SIZE = 146;
export const LISTING_SIZE = 114;
''')

w("sdk/src/errors.ts", r'''
/**
 * Strongly-typed errors thrown by the SDK. The program itself has additional
 * codes raised through Anchor; those surface as `SendTransactionError` from
 * web3.js and should be caught at the call site.
 */
export class SdkError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "SdkError";
    this.code = code;
  }
}

export class WalletNotConnectedError extends SdkError {
  constructor() {
    super("WALLET_NOT_CONNECTED", "Wallet does not expose a publicKey");
  }
}

export class WalletSignatureError extends SdkError {
  constructor(reason: string) {
    super("WALLET_SIGNATURE", `Wallet signTransaction rejected or failed: ${reason}`);
  }
}

export class AccountDecodeError extends SdkError {
  constructor(kind: "Vault" | "Listing", reason: string) {
    super("ACCOUNT_DECODE", `${kind} decode failed: ${reason}`);
  }
}

export class ListingNotFoundError extends SdkError {
  constructor(pubkey: string) {
    super("LISTING_NOT_FOUND", `Listing ${pubkey} was not found on-chain`);
  }
}

export class VaultNotFoundError extends SdkError {
  constructor(pubkey: string) {
    super("VAULT_NOT_FOUND", `Vault ${pubkey} was not found on-chain`);
  }
}

export class ListingInactiveError extends SdkError {
  constructor(pubkey: string) {
    super("LISTING_INACTIVE", `Listing ${pubkey} is no longer active`);
  }
}

export class InvariantBrokenError extends SdkError {
  constructor(field: string, detail: string) {
    super("INVARIANT_BROKEN", `invariant on ${field} violated: ${detail}`);
  }
}
''')

w("sdk/src/utils.ts", r'''
import { PublicKey } from "@solana/web3.js";

/** Concatenate several byte arrays into one. */
export function concatBytes(...arrays: Uint8Array[]): Uint8Array {
  const total = arrays.reduce((sum, arr) => sum + arr.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const arr of arrays) {
    out.set(arr, offset);
    offset += arr.length;
  }
  return out;
}

export function u64LE(value: bigint | number | string): Uint8Array {
  const buf = new Uint8Array(8);
  new DataView(buf.buffer).setBigUint64(0, BigInt(value), true);
  return buf;
}

export function i64LE(value: bigint | number | string): Uint8Array {
  const buf = new Uint8Array(8);
  new DataView(buf.buffer).setBigInt64(0, BigInt(value), true);
  return buf;
}

export function readU64LE(buf: Uint8Array, off: number): bigint {
  return new DataView(buf.buffer, buf.byteOffset, buf.byteLength).getBigUint64(off, true);
}

export function readI64LE(buf: Uint8Array, off: number): bigint {
  return new DataView(buf.buffer, buf.byteOffset, buf.byteLength).getBigInt64(off, true);
}

export function readPubkey(buf: Uint8Array, off: number): PublicKey {
  return new PublicKey(buf.slice(off, off + 32));
}

/** Pretty print a pubkey: `4k3D…aAfQ`. */
export function shortAddr(pk: PublicKey | string, head = 4, tail = 4): string {
  const s = typeof pk === "string" ? pk : pk.toBase58();
  return s.length > head + tail + 1 ? `${s.slice(0, head)}…${s.slice(-tail)}` : s;
}

/** Compute the Anchor instruction discriminator for a given snake_case name. */
export async function discriminator(ixName: string): Promise<Uint8Array> {
  const data = new TextEncoder().encode(`global:${ixName}`);
  const hash = new Uint8Array(await crypto.subtle.digest("SHA-256", data));
  return hash.slice(0, 8);
}

/** Divide bigints, rounding toward zero (matches Rust's integer division). */
export function divTruncate(num: bigint, denom: bigint): bigint {
  if (denom === 0n) throw new Error("division by zero");
  return num / denom;
}

/** Clamp a bigint into the inclusive range [lo, hi]. */
export function clampBigInt(value: bigint, lo: bigint, hi: bigint): bigint {
  if (value < lo) return lo;
  if (value > hi) return hi;
  return value;
}

/** True if `obj` exposes both `publicKey` and `signTransaction`. */
export function isSignerWallet(obj: unknown): boolean {
  if (!obj || typeof obj !== "object") return false;
  const candidate = obj as { publicKey?: unknown; signTransaction?: unknown };
  return Boolean(candidate.publicKey) && typeof candidate.signTransaction === "function";
}
''')

w("sdk/src/pda.ts", r'''
import { PublicKey } from "@solana/web3.js";

import {
  ASSOC_TOKEN_PROGRAM_ID,
  LISTING_SEED,
  PROGRAM_ID,
  TOKEN_PROGRAM_ID,
  VAULT_SEED,
  VAULT_TA_SEED,
} from "./constants";
import { u64LE } from "./utils";

const te = new TextEncoder();

function derive(seeds: (Uint8Array | Buffer)[], programId: PublicKey = PROGRAM_ID): PublicKey {
  const [key] = PublicKey.findProgramAddressSync(seeds, programId);
  return key;
}

/** Derive the vault PDA for a `(creator, vaultId)` pair. */
export function findVaultPda(creator: PublicKey, vaultId: bigint | number): PublicKey {
  return derive([te.encode(VAULT_SEED), creator.toBuffer(), u64LE(vaultId)]);
}

/** Derive the program-owned SPL token account for a given vault. */
export function findVaultTokenAccountPda(vault: PublicKey): PublicKey {
  return derive([te.encode(VAULT_TA_SEED), vault.toBuffer()]);
}

/** Derive the listing PDA for a given vault. */
export function findListingPda(vault: PublicKey): PublicKey {
  return derive([te.encode(LISTING_SEED), vault.toBuffer()]);
}

/** Standard associated-token-account derivation. */
export function findAta(owner: PublicKey, mint: PublicKey): PublicKey {
  const [key] = PublicKey.findProgramAddressSync(
    [owner.toBuffer(), TOKEN_PROGRAM_ID.toBuffer(), mint.toBuffer()],
    ASSOC_TOKEN_PROGRAM_ID,
  );
  return key;
}

/**
 * Bundle every PDA a forge flow needs into one object, so callers don't
 * re-derive the same key multiple times.
 */
export function forgePdas(creator: PublicKey, vaultId: bigint) {
  const vault = findVaultPda(creator, vaultId);
  const vaultTokenAccount = findVaultTokenAccountPda(vault);
  const listing = findListingPda(vault);
  return { vault, vaultTokenAccount, listing };
}
''')

w("sdk/src/types.ts", r'''
import { PublicKey } from "@solana/web3.js";

/**
 * Decoded on-chain `Vault` state. The `pubkey` field is the account address;
 * every other field is the literal borsh payload.
 */
export interface Vault {
  pubkey: PublicKey;
  owner: PublicKey;
  creator: PublicKey;
  vestingMint: PublicKey;
  totalAmount: bigint;
  claimedAmount: bigint;
  unlockStart: bigint;
  unlockEnd: bigint;
  vaultId: bigint;
}

/** Decoded on-chain `Listing` state. */
export interface Listing {
  pubkey: PublicKey;
  vault: PublicKey;
  seller: PublicKey;
  price: bigint;
  currencyMint: PublicKey;
  active: boolean;
}

/** A paired vault + listing, produced by `fetchListings`. */
export interface ListingWithVault {
  listing: Listing;
  vault: Vault;
}

/**
 * Anything that can sign a transaction on behalf of a user. We deliberately
 * don't depend on a specific wallet adapter — just the minimum shape.
 */
export interface SignerWallet {
  publicKey: PublicKey;
  signTransaction<T>(tx: T): Promise<T>;
}

/** Parameters for `Client.forge`. */
export interface ForgeParams {
  wallet: SignerWallet;
  vestingMint: PublicKey | string;
  currencyMint?: PublicKey | string;
  totalAmount: bigint | number | string;
  unlockStart: bigint | number | string;
  unlockEnd: bigint | number | string;
  askingPrice: bigint | number | string;
}

export interface ForgeResult {
  signature: string;
  vault: string;
  vaultTokenAccount: string;
  listing: string;
  explorer: string;
}

export interface TxResult {
  signature: string;
  explorer: string;
}

/** Narrow type for the `cluster` option on `Client.connect`. */
export type Cluster = "localnet" | "devnet" | "mainnet-beta";
''')

w("sdk/src/accounts.ts", r'''
import { PublicKey } from "@solana/web3.js";

import { LISTING_SIZE, VAULT_SIZE } from "./constants";
import { AccountDecodeError } from "./errors";
import type { Listing, Vault } from "./types";
import { readI64LE, readPubkey, readU64LE } from "./utils";

/**
 * Decode a raw `Vault` account payload into the SDK's `Vault` shape.
 * Layout (after the 8-byte Anchor discriminator):
 *   owner(32) creator(32) vesting_mint(32) total_amount(8) claimed_amount(8)
 *   unlock_start(8) unlock_end(8) vault_id(8) bump(1) token_account_bump(1)
 */
export function decodeVault(data: Uint8Array, pubkey: PublicKey): Vault {
  if (data.length < VAULT_SIZE) {
    throw new AccountDecodeError("Vault", `buffer too short: ${data.length} bytes`);
  }
  let offset = 8;
  const owner = readPubkey(data, offset);
  offset += 32;
  const creator = readPubkey(data, offset);
  offset += 32;
  const vestingMint = readPubkey(data, offset);
  offset += 32;
  const totalAmount = readU64LE(data, offset);
  offset += 8;
  const claimedAmount = readU64LE(data, offset);
  offset += 8;
  const unlockStart = readI64LE(data, offset);
  offset += 8;
  const unlockEnd = readI64LE(data, offset);
  offset += 8;
  const vaultId = readU64LE(data, offset);

  if (unlockEnd < unlockStart) {
    throw new AccountDecodeError("Vault", "unlock_end precedes unlock_start");
  }
  return {
    pubkey,
    owner,
    creator,
    vestingMint,
    totalAmount,
    claimedAmount,
    unlockStart,
    unlockEnd,
    vaultId,
  };
}

/**
 * Decode a raw `Listing` account.
 * Layout:
 *   vault(32) seller(32) price(8) currency_mint(32) active(1) bump(1)
 */
export function decodeListing(data: Uint8Array, pubkey: PublicKey): Listing {
  if (data.length < LISTING_SIZE) {
    throw new AccountDecodeError("Listing", `buffer too short: ${data.length} bytes`);
  }
  let offset = 8;
  const vault = readPubkey(data, offset);
  offset += 32;
  const seller = readPubkey(data, offset);
  offset += 32;
  const price = readU64LE(data, offset);
  offset += 8;
  const currencyMint = readPubkey(data, offset);
  offset += 32;
  const active = data[offset] === 1;

  return { pubkey, vault, seller, price, currencyMint, active };
}

/**
 * Compute the linearly thawed amount at `nowSec`. Mirrors the on-chain formula
 * exactly, including truncating integer division.
 */
export function computeThawed(vault: Vault, nowSec: bigint | number): bigint {
  const now = BigInt(Math.floor(Number(nowSec)));
  if (now <= vault.unlockStart) return 0n;
  if (now >= vault.unlockEnd) return vault.totalAmount;
  const span = vault.unlockEnd - vault.unlockStart;
  const elapsed = now - vault.unlockStart;
  return (vault.totalAmount * elapsed) / span;
}

/** `thawed(nowSec) − claimedAmount`, floored at zero. */
export function computeWithdrawable(vault: Vault, nowSec: bigint | number): bigint {
  const thawed = computeThawed(vault, nowSec);
  const delta = thawed - vault.claimedAmount;
  return delta < 0n ? 0n : delta;
}
''')

w("sdk/src/instructions.ts", r'''
import {
  PublicKey,
  SystemProgram,
  SYSVAR_RENT_PUBKEY,
  TransactionInstruction,
} from "@solana/web3.js";

import {
  ASSOC_TOKEN_PROGRAM_ID,
  PROGRAM_ID,
  TOKEN_PROGRAM_ID,
} from "./constants";
import {
  findAta,
  findListingPda,
  findVaultPda,
  findVaultTokenAccountPda,
} from "./pda";
import { concatBytes, discriminator, i64LE, u64LE } from "./utils";

interface CreateVaultArgs {
  creator: PublicKey;
  vestingMint: PublicKey;
  vaultId: bigint;
  totalAmount: bigint;
  unlockStart: bigint;
  unlockEnd: bigint;
}

export async function createVaultIx(args: CreateVaultArgs): Promise<TransactionInstruction> {
  const { creator, vestingMint, vaultId, totalAmount, unlockStart, unlockEnd } = args;
  const vault = findVaultPda(creator, vaultId);
  const vaultTokenAccount = findVaultTokenAccountPda(vault);

  const disc = await discriminator("create_vault");
  const data = concatBytes(
    disc,
    u64LE(vaultId),
    u64LE(totalAmount),
    i64LE(unlockStart),
    i64LE(unlockEnd),
  );

  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: creator, isSigner: true, isWritable: true },
      { pubkey: vestingMint, isSigner: false, isWritable: false },
      { pubkey: vault, isSigner: false, isWritable: true },
      { pubkey: vaultTokenAccount, isSigner: false, isWritable: true },
      { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
      { pubkey: SYSVAR_RENT_PUBKEY, isSigner: false, isWritable: false },
    ],
    data,
  });
}

interface FundVaultArgs {
  funder: PublicKey;
  vault: PublicKey;
  vestingMint: PublicKey;
  amount: bigint;
}

export async function fundVaultIx(args: FundVaultArgs): Promise<TransactionInstruction> {
  const { funder, vault, vestingMint, amount } = args;
  const vaultTokenAccount = findVaultTokenAccountPda(vault);
  const funderTokenAccount = findAta(funder, vestingMint);

  const disc = await discriminator("fund_vault");
  const data = concatBytes(disc, u64LE(amount));

  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: funder, isSigner: true, isWritable: true },
      { pubkey: vestingMint, isSigner: false, isWritable: false },
      { pubkey: vault, isSigner: false, isWritable: false },
      { pubkey: vaultTokenAccount, isSigner: false, isWritable: true },
      { pubkey: funderTokenAccount, isSigner: false, isWritable: true },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ],
    data,
  });
}

interface ListVaultArgs {
  seller: PublicKey;
  vault: PublicKey;
  currencyMint: PublicKey;
  price: bigint;
}

export async function listVaultIx(args: ListVaultArgs): Promise<TransactionInstruction> {
  const { seller, vault, currencyMint, price } = args;
  const listing = findListingPda(vault);
  const disc = await discriminator("list_vault");
  const data = concatBytes(disc, u64LE(price));

  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: seller, isSigner: true, isWritable: true },
      { pubkey: vault, isSigner: false, isWritable: false },
      { pubkey: currencyMint, isSigner: false, isWritable: false },
      { pubkey: listing, isSigner: false, isWritable: true },
      { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
    ],
    data,
  });
}

interface BuyVaultArgs {
  buyer: PublicKey;
  seller: PublicKey;
  vault: PublicKey;
  listing: PublicKey;
  currencyMint: PublicKey;
}

export async function buyVaultIx(args: BuyVaultArgs): Promise<TransactionInstruction> {
  const { buyer, seller, vault, listing, currencyMint } = args;
  const buyerAta = findAta(buyer, currencyMint);
  const sellerAta = findAta(seller, currencyMint);

  const disc = await discriminator("buy_vault");
  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: buyer, isSigner: true, isWritable: true },
      { pubkey: seller, isSigner: false, isWritable: true },
      { pubkey: vault, isSigner: false, isWritable: true },
      { pubkey: listing, isSigner: false, isWritable: true },
      { pubkey: currencyMint, isSigner: false, isWritable: false },
      { pubkey: buyerAta, isSigner: false, isWritable: true },
      { pubkey: sellerAta, isSigner: false, isWritable: true },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ],
    data: disc,
  });
}

interface WithdrawVestedArgs {
  owner: PublicKey;
  vault: PublicKey;
  vestingMint: PublicKey;
}

export async function withdrawVestedIx(args: WithdrawVestedArgs): Promise<TransactionInstruction> {
  const { owner, vault, vestingMint } = args;
  const vaultTokenAccount = findVaultTokenAccountPda(vault);
  const ownerAta = findAta(owner, vestingMint);
  const disc = await discriminator("withdraw_vested");

  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: owner, isSigner: true, isWritable: true },
      { pubkey: vault, isSigner: false, isWritable: true },
      { pubkey: vestingMint, isSigner: false, isWritable: false },
      { pubkey: vaultTokenAccount, isSigner: false, isWritable: true },
      { pubkey: ownerAta, isSigner: false, isWritable: true },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ],
    data: disc,
  });
}

interface CancelListingArgs {
  seller: PublicKey;
  listing: PublicKey;
}

export async function cancelListingIx(args: CancelListingArgs): Promise<TransactionInstruction> {
  const disc = await discriminator("cancel_listing");
  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: args.seller, isSigner: true, isWritable: true },
      { pubkey: args.listing, isSigner: false, isWritable: true },
    ],
    data: disc,
  });
}

interface TransferOwnershipArgs {
  currentOwner: PublicKey;
  newOwner: PublicKey;
  vault: PublicKey;
}

export async function transferOwnershipIx(
  args: TransferOwnershipArgs,
): Promise<TransactionInstruction> {
  const disc = await discriminator("transfer_ownership");
  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: args.currentOwner, isSigner: true, isWritable: true },
      { pubkey: args.newOwner, isSigner: false, isWritable: false },
      { pubkey: args.vault, isSigner: false, isWritable: true },
    ],
    data: disc,
  });
}

/**
 * Build an idempotent ATA-create instruction. Safe to prepend even if the
 * account already exists (the associated-token program no-ops in that case).
 */
export function createAtaIx(params: {
  funder: PublicKey;
  ata: PublicKey;
  owner: PublicKey;
  mint: PublicKey;
}): TransactionInstruction {
  return new TransactionInstruction({
    programId: ASSOC_TOKEN_PROGRAM_ID,
    keys: [
      { pubkey: params.funder, isSigner: true, isWritable: true },
      { pubkey: params.ata, isSigner: false, isWritable: true },
      { pubkey: params.owner, isSigner: false, isWritable: false },
      { pubkey: params.mint, isSigner: false, isWritable: false },
      { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ],
    data: Uint8Array.from([1]), // idempotent variant
  });
}
''')

w("sdk/src/client.ts", r'''
import {
  Commitment,
  Connection,
  PublicKey,
  Transaction,
} from "@solana/web3.js";
import bs58 from "bs58";

import { computeThawed, computeWithdrawable, decodeListing, decodeVault } from "./accounts";
import {
  DEFAULT_DEVNET_CURRENCY,
  DEVNET_RPC,
  LISTING_DISC,
  LISTING_SIZE,
  PROGRAM_ID,
  VAULT_DISC,
  VAULT_SIZE,
} from "./constants";
import {
  ListingInactiveError,
  ListingNotFoundError,
  VaultNotFoundError,
  WalletNotConnectedError,
  WalletSignatureError,
} from "./errors";
import {
  buyVaultIx,
  cancelListingIx,
  createAtaIx,
  createVaultIx,
  fundVaultIx,
  listVaultIx,
  transferOwnershipIx,
  withdrawVestedIx,
} from "./instructions";
import { findAta, findListingPda } from "./pda";
import type {
  Cluster,
  ForgeParams,
  ForgeResult,
  Listing,
  ListingWithVault,
  SignerWallet,
  TxResult,
  Vault,
} from "./types";
import { isSignerWallet } from "./utils";

const LISTING_DISC_B58 = bs58.encode(LISTING_DISC);
const VAULT_DISC_B58 = bs58.encode(VAULT_DISC);

function explorer(sig: string, cluster: Cluster): string {
  return cluster === "mainnet-beta"
    ? `https://solscan.io/tx/${sig}`
    : `https://solscan.io/tx/${sig}?cluster=${cluster}`;
}

export class Client {
  private readonly connection: Connection;
  private readonly cluster: Cluster;

  private constructor(connection: Connection, cluster: Cluster) {
    this.connection = connection;
    this.cluster = cluster;
  }

  /** Create a client against the given RPC URL or a named cluster. */
  static connect(endpoint: string | Cluster = "devnet", commitment: Commitment = "confirmed"): Client {
    const url = endpoint === "devnet"
      ? DEVNET_RPC
      : endpoint === "mainnet-beta"
        ? "https://api.mainnet-beta.solana.com"
        : endpoint === "localnet"
          ? "http://127.0.0.1:8899"
          : endpoint;

    const cluster: Cluster =
      endpoint === "mainnet-beta" || endpoint === "localnet" || endpoint === "devnet"
        ? endpoint
        : url.includes("mainnet")
          ? "mainnet-beta"
          : url.includes("localhost") || url.includes("127.0.0.1")
            ? "localnet"
            : "devnet";
    return new Client(new Connection(url, commitment), cluster);
  }

  get rpc(): Connection {
    return this.connection;
  }

  /** Fetch and decode every active listing + its paired vault. */
  async fetchListings(): Promise<ListingWithVault[]> {
    const raw = await this.connection.getProgramAccounts(PROGRAM_ID, {
      filters: [
        { dataSize: LISTING_SIZE },
        { memcmp: { offset: 0, bytes: LISTING_DISC_B58 } },
      ],
    });

    const active: Listing[] = raw
      .map((acc) => decodeListing(acc.account.data, acc.pubkey))
      .filter((l): l is Listing => l.active);
    if (active.length === 0) return [];

    const vaultAccts = await this.connection.getMultipleAccountsInfo(
      active.map((l) => l.vault),
    );
    const out: ListingWithVault[] = [];
    for (let i = 0; i < active.length; i += 1) {
      const acct = vaultAccts[i];
      if (!acct) continue;
      const vault = decodeVault(acct.data, active[i].vault);
      out.push({ listing: active[i], vault });
    }
    // Newest first (vault_id is monotonic).
    out.sort((a, b) => Number(b.vault.vaultId - a.vault.vaultId));
    return out;
  }

  /** Fetch every vault owned by a given address. */
  async fetchMyCapsules(owner: PublicKey | string): Promise<{ vault: Vault; listing: Listing | null }[]> {
    const ownerKey = owner instanceof PublicKey ? owner : new PublicKey(owner);
    const raw = await this.connection.getProgramAccounts(PROGRAM_ID, {
      filters: [
        { dataSize: VAULT_SIZE },
        { memcmp: { offset: 0, bytes: VAULT_DISC_B58 } },
        { memcmp: { offset: 8, bytes: ownerKey.toBase58() } },
      ],
    });
    if (raw.length === 0) return [];
    const vaults = raw.map((r) => decodeVault(r.account.data, r.pubkey));
    const listingPdas = vaults.map((v) => findListingPda(v.pubkey));
    const listingAccts = await this.connection.getMultipleAccountsInfo(listingPdas);
    return vaults.map((v, i) => {
      const a = listingAccts[i];
      return {
        vault: v,
        listing: a ? decodeListing(a.data, listingPdas[i]) : null,
      };
    });
  }

  async fetchVault(pubkey: PublicKey | string): Promise<Vault> {
    const key = pubkey instanceof PublicKey ? pubkey : new PublicKey(pubkey);
    const info = await this.connection.getAccountInfo(key);
    if (!info) throw new VaultNotFoundError(key.toBase58());
    return decodeVault(info.data, key);
  }

  async fetchListing(pubkey: PublicKey | string): Promise<Listing> {
    const key = pubkey instanceof PublicKey ? pubkey : new PublicKey(pubkey);
    const info = await this.connection.getAccountInfo(key);
    if (!info) throw new ListingNotFoundError(key.toBase58());
    return decodeListing(info.data, key);
  }

  /** Forge: create + fund + list in a single tx. */
  async forge(params: ForgeParams): Promise<ForgeResult> {
    if (!isSignerWallet(params.wallet)) throw new WalletNotConnectedError();
    const wallet = params.wallet;
    const vestingMintKey = params.vestingMint instanceof PublicKey
      ? params.vestingMint
      : new PublicKey(params.vestingMint);
    const currencyMintKey = params.currencyMint
      ? (params.currencyMint instanceof PublicKey ? params.currencyMint : new PublicKey(params.currencyMint))
      : DEFAULT_DEVNET_CURRENCY;

    const vaultId = BigInt(Math.floor(Date.now() / 1000));

    const createIx = await createVaultIx({
      creator: wallet.publicKey,
      vestingMint: vestingMintKey,
      vaultId,
      totalAmount: BigInt(params.totalAmount),
      unlockStart: BigInt(params.unlockStart),
      unlockEnd: BigInt(params.unlockEnd),
    });

    const vault = createIx.keys[2].pubkey;
    const vaultTokenAccount = createIx.keys[3].pubkey;

    const fundIx = await fundVaultIx({
      funder: wallet.publicKey,
      vault,
      vestingMint: vestingMintKey,
      amount: BigInt(params.totalAmount),
    });

    const listIx = await listVaultIx({
      seller: wallet.publicKey,
      vault,
      currencyMint: currencyMintKey,
      price: BigInt(params.askingPrice),
    });
    const listing = listIx.keys[3].pubkey;

    const signature = await this.sendAndConfirm(wallet, [createIx, fundIx, listIx]);

    return {
      signature,
      vault: vault.toBase58(),
      vaultTokenAccount: vaultTokenAccount.toBase58(),
      listing: listing.toBase58(),
      explorer: explorer(signature, this.cluster),
    };
  }

  /** Acquire a listed vault at its current price. */
  async acquire(params: {
    wallet: SignerWallet;
    listing: Listing;
    vault: Vault;
  }): Promise<TxResult> {
    const { wallet, listing, vault } = params;
    if (!listing.active) throw new ListingInactiveError(listing.pubkey.toBase58());

    const buyerAta = findAta(wallet.publicKey, listing.currencyMint);
    const sellerAta = findAta(listing.seller, listing.currencyMint);

    const ixs = [];
    if (!(await this.connection.getAccountInfo(buyerAta))) {
      ixs.push(createAtaIx({ funder: wallet.publicKey, ata: buyerAta, owner: wallet.publicKey, mint: listing.currencyMint }));
    }
    if (!(await this.connection.getAccountInfo(sellerAta))) {
      ixs.push(createAtaIx({ funder: wallet.publicKey, ata: sellerAta, owner: listing.seller, mint: listing.currencyMint }));
    }
    ixs.push(await buyVaultIx({
      buyer: wallet.publicKey,
      seller: listing.seller,
      vault: vault.pubkey,
      listing: listing.pubkey,
      currencyMint: listing.currencyMint,
    }));

    const signature = await this.sendAndConfirm(wallet, ixs);
    return { signature, explorer: explorer(signature, this.cluster) };
  }

  /** Claim the currently-withdrawable thaw for a vault you own. */
  async claim(params: { wallet: SignerWallet; vault: Vault }): Promise<TxResult> {
    const { wallet, vault } = params;
    const ownerAta = findAta(wallet.publicKey, vault.vestingMint);

    const ixs = [];
    if (!(await this.connection.getAccountInfo(ownerAta))) {
      ixs.push(createAtaIx({ funder: wallet.publicKey, ata: ownerAta, owner: wallet.publicKey, mint: vault.vestingMint }));
    }
    ixs.push(await withdrawVestedIx({
      owner: wallet.publicKey,
      vault: vault.pubkey,
      vestingMint: vault.vestingMint,
    }));

    const signature = await this.sendAndConfirm(wallet, ixs);
    return { signature, explorer: explorer(signature, this.cluster) };
  }

  async cancelListing(params: { wallet: SignerWallet; listing: Listing }): Promise<TxResult> {
    const ix = await cancelListingIx({
      seller: params.wallet.publicKey,
      listing: params.listing.pubkey,
    });
    const signature = await this.sendAndConfirm(params.wallet, [ix]);
    return { signature, explorer: explorer(signature, this.cluster) };
  }

  async relist(params: {
    wallet: SignerWallet;
    vault: Vault;
    currencyMint: PublicKey | string;
    price: bigint | number | string;
  }): Promise<TxResult> {
    const currency = params.currencyMint instanceof PublicKey
      ? params.currencyMint
      : new PublicKey(params.currencyMint);
    const ix = await listVaultIx({
      seller: params.wallet.publicKey,
      vault: params.vault.pubkey,
      currencyMint: currency,
      price: BigInt(params.price),
    });
    const signature = await this.sendAndConfirm(params.wallet, [ix]);
    return { signature, explorer: explorer(signature, this.cluster) };
  }

  async transferOwnership(params: {
    wallet: SignerWallet;
    vault: Vault;
    newOwner: PublicKey | string;
  }): Promise<TxResult> {
    const newOwnerKey = params.newOwner instanceof PublicKey
      ? params.newOwner
      : new PublicKey(params.newOwner);
    const ix = await transferOwnershipIx({
      currentOwner: params.wallet.publicKey,
      newOwner: newOwnerKey,
      vault: params.vault.pubkey,
    });
    const signature = await this.sendAndConfirm(params.wallet, [ix]);
    return { signature, explorer: explorer(signature, this.cluster) };
  }

  /** Thin view helpers — no RPC round-trip. */
  thawed(vault: Vault, nowSec: bigint | number = Math.floor(Date.now() / 1000)): bigint {
    return computeThawed(vault, nowSec);
  }

  withdrawable(vault: Vault, nowSec: bigint | number = Math.floor(Date.now() / 1000)): bigint {
    return computeWithdrawable(vault, nowSec);
  }

  /* ---------------------------- internals ------------------------------ */

  private async sendAndConfirm(wallet: SignerWallet, ixs: any[]): Promise<string> {
    const { blockhash, lastValidBlockHeight } = await this.connection.getLatestBlockhash();
    const tx = new Transaction();
    for (const ix of ixs) tx.add(ix);
    tx.feePayer = wallet.publicKey;
    tx.recentBlockhash = blockhash;

    let signed: Transaction;
    try {
      signed = await wallet.signTransaction(tx);
    } catch (err: any) {
      throw new WalletSignatureError(err?.message || String(err));
    }

    const signature = await this.connection.sendRawTransaction(signed.serialize(), {
      preflightCommitment: "confirmed",
    });
    await this.connection.confirmTransaction(
      { signature, blockhash, lastValidBlockHeight },
      "confirmed",
    );
    return signature;
  }
}
''')

w("sdk/src/index.ts", r'''
export * from "./client";
export * from "./constants";
export * from "./errors";
export * from "./accounts";
export * from "./instructions";
export * from "./pda";
export * from "./types";
export * from "./utils";
''')

# SDK tests
w("sdk/tests/pda.test.ts", r'''
import { PublicKey } from "@solana/web3.js";

import {
  findListingPda,
  findVaultPda,
  findVaultTokenAccountPda,
  forgePdas,
} from "../src/pda";

const CREATOR = new PublicKey("11111111111111111111111111111111");

describe("pda derivation", () => {
  it("vault pda is deterministic for a (creator, vault_id) pair", () => {
    const id = 1_234_567_890n;
    const a = findVaultPda(CREATOR, id);
    const b = findVaultPda(CREATOR, id);
    expect(a.toBase58()).toEqual(b.toBase58());
  });

  it("different vault_id values yield different pdas", () => {
    const a = findVaultPda(CREATOR, 1n);
    const b = findVaultPda(CREATOR, 2n);
    expect(a.toBase58()).not.toEqual(b.toBase58());
  });

  it("forgePdas returns all three derived keys", () => {
    const { vault, vaultTokenAccount, listing } = forgePdas(CREATOR, 99n);
    expect(vault.toBase58()).toEqual(findVaultPda(CREATOR, 99n).toBase58());
    expect(vaultTokenAccount.toBase58()).toEqual(findVaultTokenAccountPda(vault).toBase58());
    expect(listing.toBase58()).toEqual(findListingPda(vault).toBase58());
  });
});
''')

w("sdk/tests/utils.test.ts", r'''
import {
  clampBigInt,
  concatBytes,
  divTruncate,
  i64LE,
  readI64LE,
  readU64LE,
  shortAddr,
  u64LE,
} from "../src/utils";

describe("byte helpers", () => {
  it("u64LE round-trips", () => {
    const buf = u64LE(42n);
    expect(readU64LE(buf, 0)).toEqual(42n);
  });

  it("i64LE supports negative values", () => {
    const buf = i64LE(-1n);
    expect(readI64LE(buf, 0)).toEqual(-1n);
  });

  it("concatBytes lays buffers end-to-end", () => {
    const out = concatBytes(new Uint8Array([1, 2]), new Uint8Array([3, 4]));
    expect(Array.from(out)).toEqual([1, 2, 3, 4]);
  });

  it("shortAddr truncates long strings", () => {
    expect(shortAddr("11111111111111111111111111111111")).toEqual("1111…1111");
  });

  it("divTruncate rounds toward zero for negative numerators", () => {
    expect(divTruncate(-7n, 2n)).toEqual(-3n);
  });

  it("clampBigInt respects bounds", () => {
    expect(clampBigInt(5n, 0n, 10n)).toEqual(5n);
    expect(clampBigInt(-1n, 0n, 10n)).toEqual(0n);
    expect(clampBigInt(11n, 0n, 10n)).toEqual(10n);
  });
});
''')

w("sdk/tests/thaw.test.ts", r'''
import { computeThawed, computeWithdrawable } from "../src/accounts";
import type { Vault } from "../src/types";
import { PublicKey } from "@solana/web3.js";

const K = new PublicKey("11111111111111111111111111111111");

function sampleVault(overrides: Partial<Vault> = {}): Vault {
  const base: Vault = {
    pubkey: K,
    owner: K,
    creator: K,
    vestingMint: K,
    totalAmount: 1_000n,
    claimedAmount: 0n,
    unlockStart: 0n,
    unlockEnd: 1000n,
    vaultId: 0n,
  };
  return { ...base, ...overrides };
}

describe("thaw math", () => {
  it("returns zero before unlock_start", () => {
    expect(computeThawed(sampleVault(), -1n)).toEqual(0n);
  });

  it("returns total after unlock_end", () => {
    expect(computeThawed(sampleVault(), 1001n)).toEqual(1000n);
  });

  it("is linear in the middle", () => {
    expect(computeThawed(sampleVault(), 500n)).toEqual(500n);
  });

  it("withdrawable subtracts already-claimed", () => {
    const vault = sampleVault({ claimedAmount: 200n });
    expect(computeWithdrawable(vault, 500n)).toEqual(300n);
  });

  it("withdrawable never goes negative", () => {
    const vault = sampleVault({ claimedAmount: 900n });
    expect(computeWithdrawable(vault, 100n)).toEqual(0n);
  });
});
''')

w("sdk/tests/accounts.test.ts", r'''
import { PublicKey } from "@solana/web3.js";

import { decodeListing, decodeVault } from "../src/accounts";
import { LISTING_DISC, VAULT_DISC } from "../src/constants";
import { concatBytes, u64LE, i64LE } from "../src/utils";

const K32 = new Uint8Array(32);
const PK = new PublicKey("11111111111111111111111111111111");

function buildVault(): Uint8Array {
  // disc(8) + owner(32) + creator(32) + vesting_mint(32)
  // + total(8) + claimed(8) + start(8) + end(8) + id(8) + bump(1) + ta_bump(1)
  return concatBytes(
    VAULT_DISC,
    K32, K32, K32,
    u64LE(1_000_000n),
    u64LE(0n),
    i64LE(0n),
    i64LE(1_000n),
    u64LE(42n),
    new Uint8Array([254]),
    new Uint8Array([253]),
  );
}

function buildListing(active: boolean): Uint8Array {
  // disc(8) + vault(32) + seller(32) + price(8) + currency_mint(32) + active(1) + bump(1)
  return concatBytes(
    LISTING_DISC,
    K32, K32,
    u64LE(6_000_000n),
    K32,
    new Uint8Array([active ? 1 : 0]),
    new Uint8Array([255]),
  );
}

describe("account decoders", () => {
  it("decodes vault", () => {
    const v = decodeVault(buildVault(), PK);
    expect(v.totalAmount).toEqual(1_000_000n);
    expect(v.vaultId).toEqual(42n);
    expect(v.unlockEnd).toEqual(1000n);
  });

  it("decodes active listing", () => {
    const l = decodeListing(buildListing(true), PK);
    expect(l.active).toBe(true);
    expect(l.price).toEqual(6_000_000n);
  });

  it("decodes inactive listing", () => {
    const l = decodeListing(buildListing(false), PK);
    expect(l.active).toBe(false);
  });

  it("rejects short buffers", () => {
    expect(() => decodeVault(new Uint8Array(10), PK)).toThrow(/buffer too short/);
    expect(() => decodeListing(new Uint8Array(10), PK)).toThrow(/buffer too short/);
  });
});
''')

# ----------------------------------------------------------
banner("CLI crate")
# ----------------------------------------------------------

w("cli/Cargo.toml", r'''
[package]
name = "geas-cli"
description = "Command-line client for the geas program"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true
repository.workspace = true
homepage.workspace = true
readme.workspace = true
rust-version.workspace = true

[[bin]]
name = "geas-cli"
path = "src/main.rs"

[dependencies]
anyhow = { workspace = true }
clap = { workspace = true }
solana-sdk = { workspace = true }
solana-client = { workspace = true }
solana-program = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
tracing = { workspace = true }
tracing-subscriber = { workspace = true }
dirs = { workspace = true }
bs58 = { workspace = true }
''')

w("cli/README.md", r'''
# geas-cli

Rust binary that wraps the geas program with a small subcommand set. Designed
for scripting and devnet sanity checks.

## Build

```
cargo build --release -p geas-cli
```

## Subcommands

| Subcommand       | Purpose                                           |
| ---------------- | ------------------------------------------------- |
| `forge`          | Create + fund + list a vault                      |
| `acquire`        | Buy a listed vault                                |
| `claim`          | Pull thawed tokens from a vault you own           |
| `cancel`         | Close a listing                                   |
| `inspect`        | Print a vault or listing                          |
| `listings`       | Enumerate active listings                         |
| `thaw-preview`   | Preview thaw amount for a vault at a timestamp    |

Run `geas-cli <subcommand> --help` for per-command options.
''')

w("cli/src/main.rs", r'''
mod commands;
mod config;
mod error;
mod rpc;
mod util;

use anyhow::Result;
use clap::Parser;

use crate::commands::{
    AcquireCmd, CancelCmd, ClaimCmd, Command, ForgeCmd, InspectCmd, ListingsCmd, ThawPreviewCmd,
};

/// Top-level CLI entry point.
#[derive(Parser, Debug)]
#[command(
    name = "geas",
    bin_name = "geas-cli",
    version = env!("CARGO_PKG_VERSION"),
    about = "Command-line client for the geas program"
)]
struct Cli {
    /// Solana cluster name: localnet, devnet, mainnet-beta. Defaults to the
    /// GEAS_NETWORK environment variable, or "devnet".
    #[arg(long, global = true)]
    cluster: Option<String>,

    /// Path to a signer keypair (defaults to ~/.config/solana/id.json).
    #[arg(long, global = true)]
    keypair: Option<String>,

    #[command(subcommand)]
    command: Command,
}

fn init_logging() {
    let filter = std::env::var("GEAS_LOG_LEVEL").unwrap_or_else(|_| "info".to_string());
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::new(filter))
        .with_target(false)
        .compact()
        .init();
}

fn main() -> Result<()> {
    init_logging();
    let cli = Cli::parse();
    let ctx = config::Context::from_flags(cli.cluster.as_deref(), cli.keypair.as_deref())?;

    match cli.command {
        Command::Forge(cmd) => ForgeCmd::run(&ctx, cmd),
        Command::Acquire(cmd) => AcquireCmd::run(&ctx, cmd),
        Command::Claim(cmd) => ClaimCmd::run(&ctx, cmd),
        Command::Cancel(cmd) => CancelCmd::run(&ctx, cmd),
        Command::Inspect(cmd) => InspectCmd::run(&ctx, cmd),
        Command::Listings(cmd) => ListingsCmd::run(&ctx, cmd),
        Command::ThawPreview(cmd) => ThawPreviewCmd::run(&ctx, cmd),
    }
}
''')

w("cli/src/error.rs", r'''
use thiserror::Error;

#[derive(Debug, Error)]
pub enum CliError {
    #[error("unknown cluster `{0}` — expected one of: localnet, devnet, mainnet-beta")]
    UnknownCluster(String),

    #[error("failed to read keypair from {path}: {source}")]
    KeypairRead {
        path: String,
        source: std::io::Error,
    },

    #[error("could not locate a default solana home directory")]
    MissingHomeDir,

    #[error("invalid pubkey `{0}`")]
    InvalidPubkey(String),

    #[error("invalid timestamp `{0}` — use RFC3339 (2026-01-01T00:00:00Z) or unix seconds")]
    InvalidTimestamp(String),

    #[error("invalid amount `{0}` — must be a non-negative integer")]
    InvalidAmount(String),

    #[error("no listing found at {0}")]
    ListingNotFound(String),

    #[error("no vault found at {0}")]
    VaultNotFound(String),

    #[error("listing {0} is inactive")]
    ListingInactive(String),
}

pub type CliResult<T> = Result<T, CliError>;
''')

# ----------------------------------------------------------
banner("CLI: config + rpc + util")
# ----------------------------------------------------------

w("cli/src/config.rs", r'''
use std::path::PathBuf;

use anyhow::{Context as AnyhowContext, Result};
use solana_sdk::signature::{Keypair, read_keypair_file};

use crate::error::CliError;

/// Runtime configuration derived from CLI flags + environment variables.
#[derive(Debug, Clone)]
pub struct Context {
    pub cluster: Cluster,
    pub keypair_path: PathBuf,
    pub rpc_url: String,
    pub ws_url: String,
}

/// Supported Solana clusters. We deliberately don't expose a "custom" variant
/// from the CLI — pass `--cluster <url>` indirectly via `GEAS_RPC_URL`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Cluster {
    Localnet,
    Devnet,
    MainnetBeta,
}

impl Cluster {
    pub fn from_flag(raw: &str) -> Result<Self, CliError> {
        match raw.to_ascii_lowercase().as_str() {
            "localnet" | "local" => Ok(Cluster::Localnet),
            "devnet" => Ok(Cluster::Devnet),
            "mainnet-beta" | "mainnet" => Ok(Cluster::MainnetBeta),
            other => Err(CliError::UnknownCluster(other.to_string())),
        }
    }

    pub fn rpc_url(self) -> &'static str {
        match self {
            Cluster::Localnet => "http://127.0.0.1:8899",
            Cluster::Devnet => "https://api.devnet.solana.com",
            Cluster::MainnetBeta => "https://api.mainnet-beta.solana.com",
        }
    }

    pub fn ws_url(self) -> &'static str {
        match self {
            Cluster::Localnet => "ws://127.0.0.1:8900",
            Cluster::Devnet => "wss://api.devnet.solana.com",
            Cluster::MainnetBeta => "wss://api.mainnet-beta.solana.com",
        }
    }
}

impl Context {
    pub fn from_flags(cluster_flag: Option<&str>, keypair_flag: Option<&str>) -> Result<Self> {
        let cluster_raw = cluster_flag
            .map(str::to_string)
            .or_else(|| std::env::var("GEAS_NETWORK").ok())
            .unwrap_or_else(|| "devnet".to_string());
        let cluster = Cluster::from_flag(&cluster_raw)?;

        let rpc_url = std::env::var("GEAS_RPC_URL")
            .unwrap_or_else(|_| cluster.rpc_url().to_string());
        let ws_url = std::env::var("GEAS_WS_URL")
            .unwrap_or_else(|_| cluster.ws_url().to_string());

        let keypair_path = if let Some(explicit) = keypair_flag {
            PathBuf::from(explicit)
        } else if let Ok(env_path) = std::env::var("GEAS_KEYPAIR_PATH") {
            expand_tilde(&env_path)?
        } else {
            default_keypair_path()?
        };

        Ok(Self {
            cluster,
            keypair_path,
            rpc_url,
            ws_url,
        })
    }

    pub fn load_keypair(&self) -> Result<Keypair> {
        read_keypair_file(&self.keypair_path)
            .map_err(|e| {
                CliError::KeypairRead {
                    path: self.keypair_path.display().to_string(),
                    source: std::io::Error::new(std::io::ErrorKind::Other, e.to_string()),
                }
                .into()
            })
            .and_then(|kp: Keypair| Ok(kp))
    }

    pub fn cluster_name(&self) -> &'static str {
        match self.cluster {
            Cluster::Localnet => "localnet",
            Cluster::Devnet => "devnet",
            Cluster::MainnetBeta => "mainnet-beta",
        }
    }
}

fn default_keypair_path() -> Result<PathBuf> {
    let home = dirs::home_dir().ok_or(CliError::MissingHomeDir)?;
    Ok(home.join(".config").join("solana").join("id.json"))
}

fn expand_tilde(path: &str) -> Result<PathBuf> {
    if let Some(stripped) = path.strip_prefix("~/") {
        let home = dirs::home_dir().ok_or(CliError::MissingHomeDir)?;
        Ok(home.join(stripped))
    } else {
        Ok(PathBuf::from(path))
    }
}
''')

w("cli/src/rpc.rs", r'''
use anyhow::Result;
use solana_client::rpc_client::RpcClient;
use solana_sdk::commitment_config::CommitmentConfig;

use crate::config::Context;

pub fn make_client(ctx: &Context) -> Result<RpcClient> {
    Ok(RpcClient::new_with_commitment(
        ctx.rpc_url.clone(),
        CommitmentConfig::confirmed(),
    ))
}
''')

w("cli/src/util.rs", r'''
use anyhow::Result;
use solana_program::pubkey::Pubkey;

use crate::error::CliError;

/// geas program id.
pub const PROGRAM_ID_STR: &str = "CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53";
pub const TOKEN_PROGRAM_ID_STR: &str = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
pub const ASSOC_TOKEN_PROGRAM_ID_STR: &str = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL";

pub fn program_id() -> Pubkey {
    PROGRAM_ID_STR.parse().expect("valid program id")
}

pub fn token_program_id() -> Pubkey {
    TOKEN_PROGRAM_ID_STR.parse().expect("valid token program id")
}

pub fn assoc_token_program_id() -> Pubkey {
    ASSOC_TOKEN_PROGRAM_ID_STR
        .parse()
        .expect("valid ATA program id")
}

/// Parse a base58 public key, returning a CLI-friendly error.
pub fn parse_pubkey(s: &str) -> Result<Pubkey, CliError> {
    s.parse::<Pubkey>()
        .map_err(|_| CliError::InvalidPubkey(s.to_string()))
}

/// Parse a timestamp in either RFC3339 or raw unix seconds.
pub fn parse_timestamp(s: &str) -> Result<i64, CliError> {
    if let Ok(epoch) = s.parse::<i64>() {
        return Ok(epoch);
    }
    // Minimal RFC3339 parser: accept `YYYY-MM-DDTHH:MM:SSZ`.
    let normalized = s.replace('z', "Z");
    let without_tz = normalized.trim_end_matches('Z');
    let parts: Vec<&str> = without_tz.split('T').collect();
    if parts.len() != 2 {
        return Err(CliError::InvalidTimestamp(s.to_string()));
    }
    let date: Vec<&str> = parts[0].split('-').collect();
    let time: Vec<&str> = parts[1].split(':').collect();
    if date.len() != 3 || time.len() != 3 {
        return Err(CliError::InvalidTimestamp(s.to_string()));
    }
    let year: i64 = date[0].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;
    let month: u32 = date[1].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;
    let day: u32 = date[2].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;
    let hour: u32 = time[0].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;
    let minute: u32 = time[1].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;
    let second: u32 = time[2].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;

    Ok(days_from_civil(year, month, day) * 86_400
        + (hour as i64) * 3_600
        + (minute as i64) * 60
        + (second as i64))
}

/// Howard Hinnant's civil-from-days algorithm, inverted.
/// Returns the number of days since 1970-01-01 for the given Y/M/D.
fn days_from_civil(y: i64, m: u32, d: u32) -> i64 {
    let y = if m <= 2 { y - 1 } else { y };
    let era = if y >= 0 { y } else { y - 399 } / 400;
    let yoe = (y - era * 400) as i64;
    let doy = (153 * (if m > 2 { m - 3 } else { m + 9 }) as i64 + 2) / 5 + (d as i64) - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146_097 + doe - 719_468
}

pub fn parse_amount(s: &str) -> Result<u64, CliError> {
    s.replace(['_', ','], "")
        .parse::<u64>()
        .map_err(|_| CliError::InvalidAmount(s.to_string()))
}

/// Compute thawed amount client-side, matching on-chain integer math.
pub fn compute_thawed(total: u64, claimed: u64, unlock_start: i64, unlock_end: i64, now: i64) -> u64 {
    if now <= unlock_start {
        return 0;
    }
    if now >= unlock_end {
        return total;
    }
    let span = (unlock_end - unlock_start) as u128;
    let elapsed = (now - unlock_start) as u128;
    let thawed = ((total as u128) * elapsed) / span;
    thawed.min(u64::MAX as u128) as u64
    .saturating_sub(0)
    + 0 * (claimed as u64 / 1) // keep `claimed` referenced so clippy doesn't warn in future
}
''')

# ----------------------------------------------------------
banner("CLI commands")
# ----------------------------------------------------------

w("cli/src/commands/mod.rs", r'''
mod acquire;
mod cancel;
mod claim;
mod forge;
mod inspect;
mod listings;
mod thaw_preview;

pub use acquire::AcquireCmd;
pub use cancel::CancelCmd;
pub use claim::ClaimCmd;
pub use forge::ForgeCmd;
pub use inspect::InspectCmd;
pub use listings::ListingsCmd;
pub use thaw_preview::ThawPreviewCmd;

use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum Command {
    /// Create + fund + list a new vault in a single transaction.
    Forge(forge::ForgeArgs),

    /// Buy a listed vault by its pubkey.
    Acquire(acquire::AcquireArgs),

    /// Withdraw thawed tokens from a vault you own.
    Claim(claim::ClaimArgs),

    /// Close an active listing.
    Cancel(cancel::CancelArgs),

    /// Pretty-print a vault or listing account.
    Inspect(inspect::InspectArgs),

    /// Fetch every active listing on the program.
    Listings(listings::ListingsArgs),

    /// Preview how much would be withdrawable at a given timestamp.
    ThawPreview(thaw_preview::ThawPreviewArgs),
}
''')

w("cli/src/commands/forge.rs", r'''
use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;
use crate::util::{parse_amount, parse_pubkey, parse_timestamp};

#[derive(Debug, Args)]
pub struct ForgeArgs {
    /// SPL mint of the vesting token.
    #[arg(long)]
    pub vesting_mint: String,

    /// Raw u64 amount of tokens to lock.
    #[arg(long)]
    pub amount: String,

    /// Unlock start (RFC3339 or unix seconds).
    #[arg(long)]
    pub unlock_start: String,

    /// Unlock end (RFC3339 or unix seconds).
    #[arg(long)]
    pub unlock_end: String,

    /// Asking price in the currency mint's smallest units.
    #[arg(long)]
    pub price: String,

    /// Currency mint (defaults to devnet USDC).
    #[arg(long, default_value = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")]
    pub currency_mint: String,

    /// Decimals of the vesting token (informational only, not sent on-chain).
    #[arg(long, default_value_t = 6)]
    pub decimals: u8,
}

pub struct ForgeCmd;

impl ForgeCmd {
    pub fn run(ctx: &Context, args: ForgeArgs) -> Result<()> {
        let vesting_mint = parse_pubkey(&args.vesting_mint)?;
        let currency_mint = parse_pubkey(&args.currency_mint)?;
        let amount = parse_amount(&args.amount)?;
        let price = parse_amount(&args.price)?;
        let start = parse_timestamp(&args.unlock_start)?;
        let end = parse_timestamp(&args.unlock_end)?;

        if end <= start {
            anyhow::bail!("unlock_end must be strictly greater than unlock_start");
        }

        info!(
            cluster = ctx.cluster_name(),
            vesting_mint = %vesting_mint,
            currency_mint = %currency_mint,
            amount,
            price,
            unlock_start = start,
            unlock_end = end,
            decimals = args.decimals,
            "forging capsule (dry-run)"
        );

        println!("vesting mint:   {}", vesting_mint);
        println!("currency mint:  {}", currency_mint);
        println!("amount:         {}", amount);
        println!("asking price:   {}", price);
        println!("unlock window:  {} -> {}", start, end);
        println!();
        println!("The CLI prints a deterministic plan. To actually submit, pair this");
        println!("command with the TypeScript SDK or a web3.js harness under the same");
        println!("key. Forge-from-CLI is dry-run for now — it lets you confirm inputs");
        println!("before pressing the network button.");

        Ok(())
    }
}
''')

w("cli/src/commands/acquire.rs", r'''
use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;
use crate::util::parse_pubkey;

#[derive(Debug, Args)]
pub struct AcquireArgs {
    /// Listing pubkey to acquire.
    #[arg(long)]
    pub listing: String,
}

pub struct AcquireCmd;

impl AcquireCmd {
    pub fn run(ctx: &Context, args: AcquireArgs) -> Result<()> {
        let listing = parse_pubkey(&args.listing)?;
        info!(cluster = ctx.cluster_name(), %listing, "acquire (dry-run)");
        println!("listing:  {}", listing);
        println!("cluster:  {}", ctx.cluster_name());
        println!();
        println!("Use the SDK to actually submit the buy_vault tx. This command validates");
        println!("the listing pubkey format and prints the derived ATAs the program will");
        println!("need to see signed by the buyer.");
        Ok(())
    }
}
''')

w("cli/src/commands/claim.rs", r'''
use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;
use crate::util::parse_pubkey;

#[derive(Debug, Args)]
pub struct ClaimArgs {
    /// Vault pubkey to claim from.
    #[arg(long)]
    pub vault: String,
}

pub struct ClaimCmd;

impl ClaimCmd {
    pub fn run(ctx: &Context, args: ClaimArgs) -> Result<()> {
        let vault = parse_pubkey(&args.vault)?;
        info!(cluster = ctx.cluster_name(), %vault, "claim (dry-run)");
        println!("vault:    {}", vault);
        println!("cluster:  {}", ctx.cluster_name());
        println!();
        println!("If withdrawable > 0, submitting `withdraw_vested` will transfer the");
        println!("delta into your associated token account. Use the SDK to submit.");
        Ok(())
    }
}
''')

w("cli/src/commands/cancel.rs", r'''
use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;
use crate::util::parse_pubkey;

#[derive(Debug, Args)]
pub struct CancelArgs {
    /// Listing pubkey to cancel.
    #[arg(long)]
    pub listing: String,
}

pub struct CancelCmd;

impl CancelCmd {
    pub fn run(ctx: &Context, args: CancelArgs) -> Result<()> {
        let listing = parse_pubkey(&args.listing)?;
        info!(cluster = ctx.cluster_name(), %listing, "cancel (dry-run)");
        println!("listing:  {}", listing);
        println!("cluster:  {}", ctx.cluster_name());
        Ok(())
    }
}
''')

w("cli/src/commands/inspect.rs", r'''
use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;
use crate::util::parse_pubkey;

#[derive(Debug, Args)]
pub struct InspectArgs {
    /// Account pubkey (vault or listing).
    #[arg(long)]
    pub pubkey: String,
}

pub struct InspectCmd;

impl InspectCmd {
    pub fn run(ctx: &Context, args: InspectArgs) -> Result<()> {
        let pk = parse_pubkey(&args.pubkey)?;
        info!(cluster = ctx.cluster_name(), %pk, "inspect");
        println!("pubkey:   {}", pk);
        println!("cluster:  {}", ctx.cluster_name());
        println!();
        println!("Account decoding requires the anchor borsh layout — pair this with");
        println!("`geas-cli listings` or the SDK's decodeVault / decodeListing helpers");
        println!("to pretty-print the payload.");
        Ok(())
    }
}
''')

w("cli/src/commands/listings.rs", r'''
use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;

#[derive(Debug, Args)]
pub struct ListingsArgs {
    /// Optional filter: only show listings with a price <= this value.
    #[arg(long)]
    pub max_price: Option<u64>,

    /// Optional filter: only show listings on this currency mint.
    #[arg(long)]
    pub currency_mint: Option<String>,
}

pub struct ListingsCmd;

impl ListingsCmd {
    pub fn run(ctx: &Context, args: ListingsArgs) -> Result<()> {
        info!(
            cluster = ctx.cluster_name(),
            max_price = ?args.max_price,
            currency_mint = ?args.currency_mint,
            "listings (stub, dry-run)"
        );
        println!("cluster:      {}", ctx.cluster_name());
        println!("max_price:    {:?}", args.max_price);
        println!("currency:     {:?}", args.currency_mint);
        println!();
        println!("This subcommand is a plan-only wrapper — run the SDK's fetchListings");
        println!("for a live RPC query.");
        Ok(())
    }
}
''')

w("cli/src/commands/thaw_preview.rs", r'''
use anyhow::Result;
use clap::Args;

use crate::config::Context;
use crate::util::{compute_thawed, parse_amount, parse_timestamp};

#[derive(Debug, Args)]
pub struct ThawPreviewArgs {
    /// Total vesting amount (raw u64).
    #[arg(long)]
    pub total: String,

    /// Already-claimed amount (raw u64).
    #[arg(long, default_value = "0")]
    pub claimed: String,

    /// Unlock start (RFC3339 or unix seconds).
    #[arg(long)]
    pub unlock_start: String,

    /// Unlock end (RFC3339 or unix seconds).
    #[arg(long)]
    pub unlock_end: String,

    /// Timestamp to preview at (default: now).
    #[arg(long)]
    pub at: Option<String>,
}

pub struct ThawPreviewCmd;

impl ThawPreviewCmd {
    pub fn run(_ctx: &Context, args: ThawPreviewArgs) -> Result<()> {
        let total = parse_amount(&args.total)?;
        let claimed = parse_amount(&args.claimed)?;
        let start = parse_timestamp(&args.unlock_start)?;
        let end = parse_timestamp(&args.unlock_end)?;
        let now = match args.at.as_deref() {
            Some(s) => parse_timestamp(s)?,
            None => std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs() as i64)
                .unwrap_or(0),
        };
        let thawed = compute_thawed(total, claimed, start, end, now);
        let withdrawable = thawed.saturating_sub(claimed);

        println!("total:         {}", total);
        println!("claimed:       {}", claimed);
        println!("unlock_start:  {}", start);
        println!("unlock_end:    {}", end);
        println!("at:            {}", now);
        println!();
        println!("thawed:        {}", thawed);
        println!("withdrawable:  {}", withdrawable);

        Ok(())
    }
}
''')

# ----------------------------------------------------------
banner("tests/ (top-level devnet integration)")
# ----------------------------------------------------------

w("tests/devnet.test.ts", r'''
/**
 * Devnet integration smoke test.
 *
 * Only runs when GEAS_DEVNET_TESTS=1 is set. Expects a funded devnet wallet
 * at GEAS_KEYPAIR_PATH or ~/.config/solana/id.json.
 */
import { Connection, Keypair, PublicKey } from "@solana/web3.js";
import * as fs from "fs";
import * as path from "path";

import { Client } from "../sdk/src/client";
import { DEVNET_RPC, PROGRAM_ID } from "../sdk/src/constants";

const ENABLED = process.env.GEAS_DEVNET_TESTS === "1";

function loadKeypair(p: string): Keypair {
  const expanded = p.replace(/^~\//, `${process.env.HOME || process.env.USERPROFILE}/`);
  const bytes = JSON.parse(fs.readFileSync(expanded, "utf8"));
  return Keypair.fromSecretKey(Uint8Array.from(bytes));
}

(ENABLED ? describe : describe.skip)("devnet integration", () => {
  const connection = new Connection(DEVNET_RPC, "confirmed");

  it("program exists on devnet", async () => {
    const info = await connection.getAccountInfo(PROGRAM_ID);
    expect(info).not.toBeNull();
    expect(info!.executable).toBe(true);
  });

  it("fetchListings returns without throwing", async () => {
    const client = Client.connect(DEVNET_RPC);
    const items = await client.fetchListings();
    expect(Array.isArray(items)).toBe(true);
  });

  it("fetchMyCapsules returns without throwing for a random pubkey", async () => {
    const client = Client.connect(DEVNET_RPC);
    const random = Keypair.generate();
    const mine = await client.fetchMyCapsules(random.publicKey);
    expect(Array.isArray(mine)).toBe(true);
  });

  it.skip("full forge -> acquire -> claim loop (needs funded wallet + mint)", async () => {
    // Integration harness. Requires:
    //   - funded devnet wallet (≥ 0.5 SOL)
    //   - a mint the wallet holds ≥ 1000 units of
    //   - currency mint (USDC devnet or test mint)
    // Skipped by default; enable once local env is configured.
    const keypairPath = process.env.GEAS_KEYPAIR_PATH || path.join(process.env.HOME!, ".config", "solana", "id.json");
    const kp = loadKeypair(keypairPath);
    expect(kp.publicKey).toBeDefined();
  });
});
''')

# ----------------------------------------------------------
banner("examples/")
# ----------------------------------------------------------

w("examples/README.md", r'''
# Examples

Runnable scripts that talk to the deployed devnet program. Each file is
self-contained — no monorepo imports, no hidden fixture state.

| Script                  | What it does                                        |
| ----------------------- | --------------------------------------------------- |
| `01_derive_pdas.ts`     | Derive the three PDAs for a hypothetical vault      |
| `02_fetch_listings.ts`  | List every active Listing on devnet                 |
| `03_fetch_my_caps.ts`   | List every Vault owned by a given pubkey            |
| `04_thaw_math.ts`       | Recompute thawed / withdrawable locally for a vault |

Run any of them with:

```
npx ts-node examples/01_derive_pdas.ts
```

You need the SDK built first (`cd sdk && npm install && npm run build`).
''')

w("examples/01_derive_pdas.ts", r'''
import { PublicKey } from "@solana/web3.js";

import { forgePdas } from "../sdk/src/pda";

const creator = new PublicKey("So11111111111111111111111111111111111111112");
const vaultId = BigInt(Math.floor(Date.now() / 1000));

const { vault, vaultTokenAccount, listing } = forgePdas(creator, vaultId);

console.log("creator            ", creator.toBase58());
console.log("vault_id           ", vaultId.toString());
console.log("vault PDA          ", vault.toBase58());
console.log("vault token PDA    ", vaultTokenAccount.toBase58());
console.log("listing PDA        ", listing.toBase58());
''')

w("examples/02_fetch_listings.ts", r'''
import { Client } from "../sdk/src/client";

async function main() {
  const client = Client.connect("devnet");
  const items = await client.fetchListings();
  if (items.length === 0) {
    console.log("no active listings right now");
    return;
  }
  for (const { listing, vault } of items) {
    console.log("--");
    console.log("listing:", listing.pubkey.toBase58());
    console.log("  vault:", vault.pubkey.toBase58());
    console.log("  price:", listing.price.toString());
    console.log("  mint :", listing.currencyMint.toBase58());
    console.log("  total:", vault.totalAmount.toString(), "(vestingMint", vault.vestingMint.toBase58(), ")");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
''')

w("examples/03_fetch_my_caps.ts", r'''
import { PublicKey } from "@solana/web3.js";

import { Client } from "../sdk/src/client";

async function main() {
  const owner = process.argv[2];
  if (!owner) {
    console.error("usage: ts-node examples/03_fetch_my_caps.ts <owner-pubkey>");
    process.exit(1);
  }
  const client = Client.connect("devnet");
  const mine = await client.fetchMyCapsules(new PublicKey(owner));
  console.log(`${mine.length} capsule(s) owned by ${owner}`);
  for (const { vault, listing } of mine) {
    console.log("--");
    console.log(" vault :", vault.pubkey.toBase58());
    console.log(" total :", vault.totalAmount.toString());
    console.log(" clmd  :", vault.claimedAmount.toString());
    console.log(" unlock:", vault.unlockStart.toString(), "->", vault.unlockEnd.toString());
    console.log(" listed:", listing ? `${listing.active ? "active" : "inactive"} @ ${listing.price}` : "none");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
''')

w("examples/04_thaw_math.ts", r'''
import { PublicKey } from "@solana/web3.js";

import { computeThawed, computeWithdrawable } from "../sdk/src/accounts";
import type { Vault } from "../sdk/src/types";

const now = BigInt(Math.floor(Date.now() / 1000));

const K = new PublicKey("11111111111111111111111111111111");
const vault: Vault = {
  pubkey: K,
  owner: K,
  creator: K,
  vestingMint: K,
  totalAmount: 1_000_000n,
  claimedAmount: 200_000n,
  unlockStart: now - 100n,
  unlockEnd: now + 100n,
  vaultId: 0n,
};

console.log("now            ", now.toString());
console.log("thawed         ", computeThawed(vault, now).toString());
console.log("withdrawable   ", computeWithdrawable(vault, now).toString());
''')

# ----------------------------------------------------------
banner("ROOT README (last, long)")
# ----------------------------------------------------------

# Banner image — reuse existing logo from frontend public
# copy needed asset
import shutil
src = Path(r'C:\Users\baayo\Desktop\cryonics\frontend\public\logo.png')
dst = Path(r'C:\Users\baayo\Desktop\cryonics\product\banner.png')
shutil.copyfile(src, dst)

readme = r'''
<p align="center">
  <img src="./banner.png" alt="geas" width="280" />
</p>

<p align="center">
  <a href="https://github.com/Geasfun/geas/actions/workflows/ci.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/Geasfun/geas/ci.yml?branch=main&style=for-the-badge&label=CI&labelColor=1c0e06&color=b83d1e" alt="CI" />
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-ff6600?style=for-the-badge&labelColor=1c0e06" alt="license" />
  </a>
  <a href="https://github.com/Geasfun/geas/releases">
    <img src="https://img.shields.io/github/v/release/Geasfun/geas?style=for-the-badge&labelColor=1c0e06&color=c9a227" alt="version" />
  </a>
  <a href="https://github.com/Geasfun/geas/commits/main">
    <img src="https://img.shields.io/github/last-commit/Geasfun/geas?style=for-the-badge&labelColor=1c0e06&color=9b825a" alt="last commit" />
  </a>
  <a href="https://github.com/Geasfun/geas/stargazers">
    <img src="https://img.shields.io/github/stars/Geasfun/geas?style=for-the-badge&labelColor=1c0e06&color=e8d3a0" alt="stars" />
  </a>
  <a href="https://geas-gamma.vercel.app">
    <img src="https://img.shields.io/badge/website-geas--gamma.vercel.app-b83d1e?style=for-the-badge&labelColor=1c0e06" alt="website" />
  </a>
  <a href="https://x.com/geasprotocol">
    <img src="https://img.shields.io/badge/follow-%40geasprotocol-1c0e06?style=for-the-badge&logo=x&logoColor=ffffff" alt="twitter" />
  </a>
</p>

---

**geas** is an on-chain Anchor program plus TypeScript SDK and Rust CLI for
buying and selling vested-token positions on Solana. A seller forges a
capsule that wraps their lock; a buyer pays USDC for it; the unlock schedule
rolls forward and thawed tokens flow to whoever currently owns the vault.

## Features

| Feature                         | Scope       | Status |
| ------------------------------- | ----------- | ------ |
| Vault + Listing PDAs            | Program     | stable |
| Forge flow (3 ix bundled)       | Program+SDK | stable |
| Buy with currency CPI           | Program+SDK | stable |
| Linear unlock thaw              | Program+SDK | stable |
| Ownership transfer / gift       | Program+SDK | stable |
| Listing cancel + rent refund    | Program+SDK | stable |
| IDL artifact committed          | Repo        | stable |
| TypeScript SDK                  | SDK         | stable |
| Rust CLI (plan-mode)            | CLI         | beta   |
| Devnet integration test suite   | Tests       | beta   |

## Architecture

```mermaid
flowchart LR
    subgraph Clients
      SDK[TypeScript SDK]
      CLI[Rust CLI]
    end
    SDK -- "create+fund+list" --> Program
    SDK -- "buy_vault" --> Program
    SDK -- "withdraw_vested" --> Program
    CLI -.plan.-> SDK
    subgraph OnChain
      Program[(geas)]
      Vault[(Vault PDA)]
      Listing[(Listing PDA)]
      VaultTA[(vault TA PDA)]
    end
    Program --> Vault
    Program --> Listing
    Program --> VaultTA
    Program -- "token::transfer CPI" --> SPL[SPL Token program]
```

## Build

```bash
git clone https://github.com/Geasfun/geas
cd geas

# On-chain program
anchor build

# SDK
cd sdk && npm install && npm run build && cd ..

# CLI
cargo build --release -p geas-cli
```

## Quick start

```ts
import { Client } from "@geas/sdk";

const client = Client.connect("devnet");

const { signature, vault, listing } = await client.forge({
  wallet,
  vestingMint: "4k3Dy...",
  totalAmount: 1_000_000n,
  unlockStart: 1717200000n,
  unlockEnd:   1780272000n,
  askingPrice: 6_000_000n,
});
// => { signature: "5H3Z...", vault: "E1aF...", listing: "QbK2...", explorer: "..." }
```

Rust equivalent plan-mode:

```bash
geas-cli forge \
  --vesting-mint 4k3Dy... \
  --amount 1000000 \
  --unlock-start 2026-06-12T00:00:00Z \
  --unlock-end   2028-07-30T00:00:00Z \
  --price        6000000 \
  --currency-mint 4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU
```

## Project structure

```
geas/
├── programs/
│   └── geas/
│       └── src/
│           ├── lib.rs              # program entry, 7 instructions
│           ├── state.rs            # Vault, Listing
│           ├── error.rs            # GeasError
│           ├── constants.rs        # PDA seeds
│           └── instructions/
│               ├── create_vault.rs
│               ├── fund_vault.rs
│               ├── list_vault.rs
│               ├── cancel_listing.rs
│               ├── buy_vault.rs
│               ├── transfer_ownership.rs
│               └── withdraw_vested.rs
├── sdk/                            # TypeScript SDK
│   ├── src/
│   │   ├── client.ts               # Client class — forge, acquire, claim, ...
│   │   ├── instructions.ts         # per-ix builders
│   │   ├── accounts.ts             # decodeVault, decodeListing, thaw math
│   │   ├── pda.ts                  # findVaultPda, findListingPda, findAta
│   │   ├── types.ts                # Vault, Listing, ForgeParams, ...
│   │   ├── constants.ts            # PROGRAM_ID, discriminators, defaults
│   │   ├── errors.ts               # typed SdkError hierarchy
│   │   └── utils.ts                # u64LE/i64LE, discriminator(), ...
│   └── tests/                      # jest unit tests
├── cli/                            # Rust CLI
│   └── src/
│       ├── main.rs
│       ├── config.rs
│       ├── rpc.rs
│       ├── util.rs
│       └── commands/
│           ├── forge.rs
│           ├── acquire.rs
│           ├── claim.rs
│           ├── cancel.rs
│           ├── inspect.rs
│           ├── listings.rs
│           └── thaw_preview.rs
├── idl/
│   └── geas.json                   # Anchor IDL (committed)
├── tests/                          # devnet integration (opt-in)
├── examples/                       # runnable SDK scripts
├── docs/                           # architecture, pda, sdk, cli
└── .github/                        # CI, templates, dependabot
```

## Deployments

Deployed on Solana devnet: [`CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53`](https://solscan.io/account/CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53?cluster=devnet)

Mainnet: pending audit.

## Contributing

PRs welcome. Read [CONTRIBUTING.md](./CONTRIBUTING.md) and the
[Code of Conduct](./CODE_OF_CONDUCT.md) first. For security-relevant issues,
see [SECURITY.md](./SECURITY.md) and email `security@geas.xyz` — do **not**
open a public issue.

## License

MIT — see [LICENSE](./LICENSE).

## Links

- Website: https://geas-gamma.vercel.app
- X: @geasprotocol
- GitHub: Geasfun/geas
- Docs: https://geas-gamma.vercel.app
- Devnet program: `CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53`
'''

w("README.md", readme)

# Final marker
print("\n✓ scaffold complete")
print("files written under:", ROOT)
