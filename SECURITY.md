# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.4.x   | Yes       |
| 0.3.x   | Critical fixes only |
| < 0.3   | No        |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for a suspected security bug.

Email a description with a reproducer to `security@geas.fun`. If the report
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
