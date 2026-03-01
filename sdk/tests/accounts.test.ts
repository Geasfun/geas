import { PublicKey } from "@solana/web3.js";

import { decodeListing, decodeVault } from "../src/accounts";
import { LISTING_DISC, VAULT_DISC } from "../src/constants";
import { concatBytes, u64LE, i64LE } from "../src/utils";

const K32 = new Uint8Array(32);
const PK = new PublicKey("11111111111111111111111111111111");

function buildVault(): Uint8Array {
  // disc(8) + owner(32) + creator(32) + vesting_mint(32)
  // + total(8) + claimed(8) + start(8) + end(8) + id(8) + bump(1) + ta_bump(1)
  return concatBytes(
    VAULT_DISC,
    K32, K32, K32,
    u64LE(1_000_000n),
    u64LE(0n),
    i64LE(0n),
    i64LE(1_000n),
    u64LE(42n),
    new Uint8Array([254]),
    new Uint8Array([253]),
  );
}

function buildListing(active: boolean): Uint8Array {
  // disc(8) + vault(32) + seller(32) + price(8) + currency_mint(32) + active(1) + bump(1)
  return concatBytes(
    LISTING_DISC,
    K32, K32,
    u64LE(6_000_000n),
    K32,
    new Uint8Array([active ? 1 : 0]),
    new Uint8Array([255]),
  );
}

describe("account decoders", () => {
  it("decodes vault", () => {
    const v = decodeVault(buildVault(), PK);
    expect(v.totalAmount).toEqual(1_000_000n);
    expect(v.vaultId).toEqual(42n);
    expect(v.unlockEnd).toEqual(1000n);
  });

  it("decodes active listing", () => {
    const l = decodeListing(buildListing(true), PK);
    expect(l.active).toBe(true);
    expect(l.price).toEqual(6_000_000n);
  });

  it("decodes inactive listing", () => {
    const l = decodeListing(buildListing(false), PK);
    expect(l.active).toBe(false);
  });

  it("rejects short buffers", () => {
    expect(() => decodeVault(new Uint8Array(10), PK)).toThrow(/buffer too short/);
    expect(() => decodeListing(new Uint8Array(10), PK)).toThrow(/buffer too short/);
  });
});
