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
