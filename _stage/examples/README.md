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
