import { PublicKey } from "@solana/web3.js";

import { forgePdas } from "../sdk/src/pda";

const creator = new PublicKey("So11111111111111111111111111111111111111112");
const vaultId = BigInt(Math.floor(Date.now() / 1000));

const { vault, vaultTokenAccount, listing } = forgePdas(creator, vaultId);

console.log("creator            ", creator.toBase58());
console.log("vault_id           ", vaultId.toString());
console.log("vault PDA          ", vault.toBase58());
console.log("vault token PDA    ", vaultTokenAccount.toBase58());
console.log("listing PDA        ", listing.toBase58());
