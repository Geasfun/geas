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
