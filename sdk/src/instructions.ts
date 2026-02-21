import {
  PublicKey,
  SystemProgram,
  SYSVAR_RENT_PUBKEY,
  TransactionInstruction,
} from "@solana/web3.js";

import {
  ASSOC_TOKEN_PROGRAM_ID,
  PROGRAM_ID,
  TOKEN_PROGRAM_ID,
} from "./constants";
import {
  findAta,
  findListingPda,
  findVaultPda,
  findVaultTokenAccountPda,
} from "./pda";
import { concatBytes, discriminator, i64LE, u64LE } from "./utils";

interface CreateVaultArgs {
  creator: PublicKey;
  vestingMint: PublicKey;
  vaultId: bigint;
  totalAmount: bigint;
  unlockStart: bigint;
  unlockEnd: bigint;
}

export async function createVaultIx(args: CreateVaultArgs): Promise<TransactionInstruction> {
  const { creator, vestingMint, vaultId, totalAmount, unlockStart, unlockEnd } = args;
  const vault = findVaultPda(creator, vaultId);
  const vaultTokenAccount = findVaultTokenAccountPda(vault);

  const disc = await discriminator("create_vault");
  const data = concatBytes(
    disc,
    u64LE(vaultId),
    u64LE(totalAmount),
    i64LE(unlockStart),
    i64LE(unlockEnd),
  );

  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: creator, isSigner: true, isWritable: true },
      { pubkey: vestingMint, isSigner: false, isWritable: false },
      { pubkey: vault, isSigner: false, isWritable: true },
      { pubkey: vaultTokenAccount, isSigner: false, isWritable: true },
      { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
      { pubkey: SYSVAR_RENT_PUBKEY, isSigner: false, isWritable: false },
    ],
    data,
  });
}

interface FundVaultArgs {
  funder: PublicKey;
  vault: PublicKey;
  vestingMint: PublicKey;
  amount: bigint;
}

export async function fundVaultIx(args: FundVaultArgs): Promise<TransactionInstruction> {
  const { funder, vault, vestingMint, amount } = args;
  const vaultTokenAccount = findVaultTokenAccountPda(vault);
  const funderTokenAccount = findAta(funder, vestingMint);

  const disc = await discriminator("fund_vault");
  const data = concatBytes(disc, u64LE(amount));

  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: funder, isSigner: true, isWritable: true },
      { pubkey: vestingMint, isSigner: false, isWritable: false },
      { pubkey: vault, isSigner: false, isWritable: false },
      { pubkey: vaultTokenAccount, isSigner: false, isWritable: true },
      { pubkey: funderTokenAccount, isSigner: false, isWritable: true },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ],
    data,
  });
}

interface ListVaultArgs {
  seller: PublicKey;
  vault: PublicKey;
  currencyMint: PublicKey;
  price: bigint;
}

export async function listVaultIx(args: ListVaultArgs): Promise<TransactionInstruction> {
  const { seller, vault, currencyMint, price } = args;
  const listing = findListingPda(vault);
  const disc = await discriminator("list_vault");
  const data = concatBytes(disc, u64LE(price));

  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: seller, isSigner: true, isWritable: true },
      { pubkey: vault, isSigner: false, isWritable: false },
      { pubkey: currencyMint, isSigner: false, isWritable: false },
      { pubkey: listing, isSigner: false, isWritable: true },
      { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
    ],
    data,
  });
}

interface BuyVaultArgs {
  buyer: PublicKey;
  seller: PublicKey;
  vault: PublicKey;
  listing: PublicKey;
  currencyMint: PublicKey;
}

export async function buyVaultIx(args: BuyVaultArgs): Promise<TransactionInstruction> {
  const { buyer, seller, vault, listing, currencyMint } = args;
  const buyerAta = findAta(buyer, currencyMint);
  const sellerAta = findAta(seller, currencyMint);

  const disc = await discriminator("buy_vault");
  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: buyer, isSigner: true, isWritable: true },
      { pubkey: seller, isSigner: false, isWritable: true },
      { pubkey: vault, isSigner: false, isWritable: true },
      { pubkey: listing, isSigner: false, isWritable: true },
      { pubkey: currencyMint, isSigner: false, isWritable: false },
      { pubkey: buyerAta, isSigner: false, isWritable: true },
      { pubkey: sellerAta, isSigner: false, isWritable: true },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ],
    data: disc,
  });
}

interface WithdrawVestedArgs {
  owner: PublicKey;
  vault: PublicKey;
  vestingMint: PublicKey;
}

export async function withdrawVestedIx(args: WithdrawVestedArgs): Promise<TransactionInstruction> {
  const { owner, vault, vestingMint } = args;
  const vaultTokenAccount = findVaultTokenAccountPda(vault);
  const ownerAta = findAta(owner, vestingMint);
  const disc = await discriminator("withdraw_vested");

  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: owner, isSigner: true, isWritable: true },
      { pubkey: vault, isSigner: false, isWritable: true },
      { pubkey: vestingMint, isSigner: false, isWritable: false },
      { pubkey: vaultTokenAccount, isSigner: false, isWritable: true },
      { pubkey: ownerAta, isSigner: false, isWritable: true },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ],
    data: disc,
  });
}

interface CancelListingArgs {
  seller: PublicKey;
  listing: PublicKey;
}

export async function cancelListingIx(args: CancelListingArgs): Promise<TransactionInstruction> {
  const disc = await discriminator("cancel_listing");
  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: args.seller, isSigner: true, isWritable: true },
      { pubkey: args.listing, isSigner: false, isWritable: true },
    ],
    data: disc,
  });
}

interface TransferOwnershipArgs {
  currentOwner: PublicKey;
  newOwner: PublicKey;
  vault: PublicKey;
}

export async function transferOwnershipIx(
  args: TransferOwnershipArgs,
): Promise<TransactionInstruction> {
  const disc = await discriminator("transfer_ownership");
  return new TransactionInstruction({
    programId: PROGRAM_ID,
    keys: [
      { pubkey: args.currentOwner, isSigner: true, isWritable: true },
      { pubkey: args.newOwner, isSigner: false, isWritable: false },
      { pubkey: args.vault, isSigner: false, isWritable: true },
    ],
    data: disc,
  });
}

/**
 * Build an idempotent ATA-create instruction. Safe to prepend even if the
 * account already exists (the associated-token program no-ops in that case).
 */
export function createAtaIx(params: {
  funder: PublicKey;
  ata: PublicKey;
  owner: PublicKey;
  mint: PublicKey;
}): TransactionInstruction {
  return new TransactionInstruction({
    programId: ASSOC_TOKEN_PROGRAM_ID,
    keys: [
      { pubkey: params.funder, isSigner: true, isWritable: true },
      { pubkey: params.ata, isSigner: false, isWritable: true },
      { pubkey: params.owner, isSigner: false, isWritable: false },
      { pubkey: params.mint, isSigner: false, isWritable: false },
      { pubkey: SystemProgram.programId, isSigner: false, isWritable: false },
      { pubkey: TOKEN_PROGRAM_ID, isSigner: false, isWritable: false },
    ],
    data: Uint8Array.from([1]), // idempotent variant
  });
}
