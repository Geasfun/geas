import { Client } from "../sdk/src/client";

async function main() {
  const client = Client.connect("devnet");
  const items = await client.fetchListings();
  if (items.length === 0) {
    console.log("no active listings right now");
    return;
  }
  for (const { listing, vault } of items) {
    console.log("--");
    console.log("listing:", listing.pubkey.toBase58());
    console.log("  vault:", vault.pubkey.toBase58());
    console.log("  price:", listing.price.toString());
    console.log("  mint :", listing.currencyMint.toBase58());
    console.log("  total:", vault.totalAmount.toString(), "(vestingMint", vault.vestingMint.toBase58(), ")");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
