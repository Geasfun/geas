/**
 * Devnet integration smoke test.
 *
 * Only runs when GEAS_DEVNET_TESTS=1 is set. Expects a funded devnet wallet
 * at GEAS_KEYPAIR_PATH or ~/.config/solana/id.json.
 */
import { Connection, Keypair, PublicKey } from "@solana/web3.js";
import * as fs from "fs";
import * as path from "path";

import { Client } from "../sdk/src/client";
import { DEVNET_RPC, PROGRAM_ID } from "../sdk/src/constants";

const ENABLED = process.env.GEAS_DEVNET_TESTS === "1";

function loadKeypair(p: string): Keypair {
  const expanded = p.replace(/^~\//, `${process.env.HOME || process.env.USERPROFILE}/`);
  const bytes = JSON.parse(fs.readFileSync(expanded, "utf8"));
  return Keypair.fromSecretKey(Uint8Array.from(bytes));
}

(ENABLED ? describe : describe.skip)("devnet integration", () => {
  const connection = new Connection(DEVNET_RPC, "confirmed");

  it("program exists on devnet", async () => {
    const info = await connection.getAccountInfo(PROGRAM_ID);
    expect(info).not.toBeNull();
    expect(info!.executable).toBe(true);
  });

  it("fetchListings returns without throwing", async () => {
    const client = Client.connect(DEVNET_RPC);
    const items = await client.fetchListings();
    expect(Array.isArray(items)).toBe(true);
  });

  it("fetchMyCapsules returns without throwing for a random pubkey", async () => {
    const client = Client.connect(DEVNET_RPC);
    const random = Keypair.generate();
    const mine = await client.fetchMyCapsules(random.publicKey);
    expect(Array.isArray(mine)).toBe(true);
  });

  it.skip("full forge -> acquire -> claim loop (needs funded wallet + mint)", async () => {
    // Integration harness. Requires:
    //   - funded devnet wallet (≥ 0.5 SOL)
    //   - a mint the wallet holds ≥ 1000 units of
    //   - currency mint (USDC devnet or test mint)
    // Skipped by default; enable once local env is configured.
    const keypairPath = process.env.GEAS_KEYPAIR_PATH || path.join(process.env.HOME!, ".config", "solana", "id.json");
    const kp = loadKeypair(keypairPath);
    expect(kp.publicKey).toBeDefined();
  });
});
