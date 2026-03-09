import { PublicKey } from "@solana/web3.js";

import { Client } from "../sdk/src/client";

async function main() {
  const owner = process.argv[2];
  if (!owner) {
    console.error("usage: ts-node examples/03_fetch_my_caps.ts <owner-pubkey>");
    process.exit(1);
  }
  const client = Client.connect("devnet");
  const mine = await client.fetchMyCapsules(new PublicKey(owner));
  console.log(`${mine.length} capsule(s) owned by ${owner}`);
  for (const { vault, listing } of mine) {
    console.log("--");
    console.log(" vault :", vault.pubkey.toBase58());
    console.log(" total :", vault.totalAmount.toString());
    console.log(" clmd  :", vault.claimedAmount.toString());
    console.log(" unlock:", vault.unlockStart.toString(), "->", vault.unlockEnd.toString());
    console.log(" listed:", listing ? `${listing.active ? "active" : "inactive"} @ ${listing.price}` : "none");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
