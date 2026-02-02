import { PublicKey } from "@solana/web3.js";

import {
  findListingPda,
  findVaultPda,
  findVaultTokenAccountPda,
  forgePdas,
} from "../src/pda";

const CREATOR = new PublicKey("11111111111111111111111111111111");

describe("pda derivation", () => {
  it("vault pda is deterministic for a (creator, vault_id) pair", () => {
    const id = 1_234_567_890n;
    const a = findVaultPda(CREATOR, id);
    const b = findVaultPda(CREATOR, id);
    expect(a.toBase58()).toEqual(b.toBase58());
  });

  it("different vault_id values yield different pdas", () => {
    const a = findVaultPda(CREATOR, 1n);
    const b = findVaultPda(CREATOR, 2n);
    expect(a.toBase58()).not.toEqual(b.toBase58());
  });

  it("forgePdas returns all three derived keys", () => {
    const { vault, vaultTokenAccount, listing } = forgePdas(CREATOR, 99n);
    expect(vault.toBase58()).toEqual(findVaultPda(CREATOR, 99n).toBase58());
    expect(vaultTokenAccount.toBase58()).toEqual(findVaultTokenAccountPda(vault).toBase58());
    expect(listing.toBase58()).toEqual(findListingPda(vault).toBase58());
  });
});
