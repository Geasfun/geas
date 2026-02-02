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
