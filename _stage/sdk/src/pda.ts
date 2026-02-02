import { PublicKey } from "@solana/web3.js";

import {
  ASSOC_TOKEN_PROGRAM_ID,
  LISTING_SEED,
  PROGRAM_ID,
  TOKEN_PROGRAM_ID,
  VAULT_SEED,
  VAULT_TA_SEED,
} from "./constants";
import { u64LE } from "./utils";

const te = new TextEncoder();

function derive(seeds: (Uint8Array | Buffer)[], programId: PublicKey = PROGRAM_ID): PublicKey {
  const [key] = PublicKey.findProgramAddressSync(seeds, programId);
  return key;
}

/** Derive the vault PDA for a `(creator, vaultId)` pair. */
export function findVaultPda(creator: PublicKey, vaultId: bigint | number): PublicKey {
  return derive([te.encode(VAULT_SEED), creator.toBuffer(), u64LE(vaultId)]);
}

/** Derive the program-owned SPL token account for a given vault. */
export function findVaultTokenAccountPda(vault: PublicKey): PublicKey {
  return derive([te.encode(VAULT_TA_SEED), vault.toBuffer()]);
}

/** Derive the listing PDA for a given vault. */
export function findListingPda(vault: PublicKey): PublicKey {
  return derive([te.encode(LISTING_SEED), vault.toBuffer()]);
}

/** Standard associated-token-account derivation. */
export function findAta(owner: PublicKey, mint: PublicKey): PublicKey {
  const [key] = PublicKey.findProgramAddressSync(
    [owner.toBuffer(), TOKEN_PROGRAM_ID.toBuffer(), mint.toBuffer()],
    ASSOC_TOKEN_PROGRAM_ID,
  );
  return key;
}

/**
 * Bundle every PDA a forge flow needs into one object, so callers don't
 * re-derive the same key multiple times.
 */
export function forgePdas(creator: PublicKey, vaultId: bigint) {
  const vault = findVaultPda(creator, vaultId);
  const vaultTokenAccount = findVaultTokenAccountPda(vault);
  const listing = findListingPda(vault);
  return { vault, vaultTokenAccount, listing };
}
