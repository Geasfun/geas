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
