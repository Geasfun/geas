import { PublicKey } from "@solana/web3.js";

/**
 * Decoded on-chain `Vault` state. The `pubkey` field is the account address;
 * every other field is the literal borsh payload.
 */
export interface Vault {
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

/** Decoded on-chain `Listing` state. */
export interface Listing {
  pubkey: PublicKey;
  vault: PublicKey;
  seller: PublicKey;
  price: bigint;
  currencyMint: PublicKey;
  active: boolean;
}

/** A paired vault + listing, produced by `fetchListings`. */
export interface ListingWithVault {
  listing: Listing;
  vault: Vault;
}

/**
 * Anything that can sign a transaction on behalf of a user. We deliberately
 * don't depend on a specific wallet adapter — just the minimum shape.
 */
export interface SignerWallet {
  publicKey: PublicKey;
  signTransaction<T>(tx: T): Promise<T>;
}

/** Parameters for `Client.forge`. */
export interface ForgeParams {
  wallet: SignerWallet;
  vestingMint: PublicKey | string;
  currencyMint?: PublicKey | string;
  totalAmount: bigint | number | string;
  unlockStart: bigint | number | string;
  unlockEnd: bigint | number | string;
  askingPrice: bigint | number | string;
}

export interface ForgeResult {
  signature: string;
  vault: string;
  vaultTokenAccount: string;
  listing: string;
  explorer: string;
}

export interface TxResult {
  signature: string;
  explorer: string;
}

/** Narrow type for the `cluster` option on `Client.connect`. */
export type Cluster = "localnet" | "devnet" | "mainnet-beta";
