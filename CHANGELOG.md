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
