import { PublicKey } from "@solana/web3.js";

import { computeThawed, computeWithdrawable } from "../sdk/src/accounts";
import type { Vault } from "../sdk/src/types";

const now = BigInt(Math.floor(Date.now() / 1000));

const K = new PublicKey("11111111111111111111111111111111");
const vault: Vault = {
  pubkey: K,
  owner: K,
  creator: K,
  vestingMint: K,
  totalAmount: 1_000_000n,
  claimedAmount: 200_000n,
  unlockStart: now - 100n,
  unlockEnd: now + 100n,
  vaultId: 0n,
};

console.log("now            ", now.toString());
console.log("thawed         ", computeThawed(vault, now).toString());
console.log("withdrawable   ", computeWithdrawable(vault, now).toString());
