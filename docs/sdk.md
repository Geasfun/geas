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
