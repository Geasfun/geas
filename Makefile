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
