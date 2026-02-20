import { PublicKey } from "@solana/web3.js";

import { LISTING_SIZE, VAULT_SIZE } from "./constants";
import { AccountDecodeError } from "./errors";
import type { Listing, Vault } from "./types";
import { readI64LE, readPubkey, readU64LE } from "./utils";

/**
 * Decode a raw `Vault` account payload into the SDK's `Vault` shape.
 * Layout (after the 8-byte Anchor discriminator):
 *   owner(32) creator(32) vesting_mint(32) total_amount(8) claimed_amount(8)
 *   unlock_start(8) unlock_end(8) vault_id(8) bump(1) token_account_bump(1)
 */
export function decodeVault(data: Uint8Array, pubkey: PublicKey): Vault {
  if (data.length < VAULT_SIZE) {
    throw new AccountDecodeError("Vault", `buffer too short: ${data.length} bytes`);
  }
  let offset = 8;
  const owner = readPubkey(data, offset);
  offset += 32;
  const creator = readPubkey(data, offset);
  offset += 32;
  const vestingMint = readPubkey(data, offset);
  offset += 32;
  const totalAmount = readU64LE(data, offset);
  offset += 8;
  const claimedAmount = readU64LE(data, offset);
  offset += 8;
  const unlockStart = readI64LE(data, offset);
  offset += 8;
  const unlockEnd = readI64LE(data, offset);
  offset += 8;
  const vaultId = readU64LE(data, offset);

  if (unlockEnd < unlockStart) {
    throw new AccountDecodeError("Vault", "unlock_end precedes unlock_start");
  }
  return {
    pubkey,
    owner,
    creator,
    vestingMint,
    totalAmount,
    claimedAmount,
    unlockStart,
    unlockEnd,
    vaultId,
  };
}

/**
 * Decode a raw `Listing` account.
 * Layout:
 *   vault(32) seller(32) price(8) currency_mint(32) active(1) bump(1)
 */
export function decodeListing(data: Uint8Array, pubkey: PublicKey): Listing {
  if (data.length < LISTING_SIZE) {
    throw new AccountDecodeError("Listing", `buffer too short: ${data.length} bytes`);
  }
  let offset = 8;
  const vault = readPubkey(data, offset);
  offset += 32;
  const seller = readPubkey(data, offset);
  offset += 32;
  const price = readU64LE(data, offset);
  offset += 8;
  const currencyMint = readPubkey(data, offset);
  offset += 32;
  const active = data[offset] === 1;

  return { pubkey, vault, seller, price, currencyMint, active };
}

/**
 * Compute the linearly thawed amount at `nowSec`. Mirrors the on-chain formula
 * exactly, including truncating integer division.
 */
export function computeThawed(vault: Vault, nowSec: bigint | number): bigint {
  const now = BigInt(Math.floor(Number(nowSec)));
  if (now <= vault.unlockStart) return 0n;
  if (now >= vault.unlockEnd) return vault.totalAmount;
  const span = vault.unlockEnd - vault.unlockStart;
  const elapsed = now - vault.unlockStart;
  return (vault.totalAmount * elapsed) / span;
}

/** `thawed(nowSec) − claimedAmount`, floored at zero. */
export function computeWithdrawable(vault: Vault, nowSec: bigint | number): bigint {
  const thawed = computeThawed(vault, nowSec);
  const delta = thawed - vault.claimedAmount;
  return delta < 0n ? 0n : delta;
}
