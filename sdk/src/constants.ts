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
