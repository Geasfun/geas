import { computeThawed, computeWithdrawable } from "../src/accounts";
import type { Vault } from "../src/types";
import { PublicKey } from "@solana/web3.js";

const K = new PublicKey("11111111111111111111111111111111");

function sampleVault(overrides: Partial<Vault> = {}): Vault {
  const base: Vault = {
    pubkey: K,
    owner: K,
    creator: K,
    vestingMint: K,
    totalAmount: 1_000n,
    claimedAmount: 0n,
    unlockStart: 0n,
    unlockEnd: 1000n,
    vaultId: 0n,
  };
  return { ...base, ...overrides };
}

describe("thaw math", () => {
  it("returns zero before unlock_start", () => {
    expect(computeThawed(sampleVault(), -1n)).toEqual(0n);
  });

  it("returns total after unlock_end", () => {
    expect(computeThawed(sampleVault(), 1001n)).toEqual(1000n);
  });

  it("is linear in the middle", () => {
    expect(computeThawed(sampleVault(), 500n)).toEqual(500n);
  });

  it("withdrawable subtracts already-claimed", () => {
    const vault = sampleVault({ claimedAmount: 200n });
    expect(computeWithdrawable(vault, 500n)).toEqual(300n);
  });

  it("withdrawable never goes negative", () => {
    const vault = sampleVault({ claimedAmount: 900n });
    expect(computeWithdrawable(vault, 100n)).toEqual(0n);
  });
});
