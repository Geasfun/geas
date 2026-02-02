import {
  Commitment,
  Connection,
  PublicKey,
  Transaction,
} from "@solana/web3.js";
import bs58 from "bs58";

import { computeThawed, computeWithdrawable, decodeListing, decodeVault } from "./accounts";
import {
  DEFAULT_DEVNET_CURRENCY,
  DEVNET_RPC,
  LISTING_DISC,
  LISTING_SIZE,
  PROGRAM_ID,
  VAULT_DISC,
  VAULT_SIZE,
} from "./constants";
import {
  ListingInactiveError,
  ListingNotFoundError,
  VaultNotFoundError,
  WalletNotConnectedError,
  WalletSignatureError,
} from "./errors";
import {
  buyVaultIx,
  cancelListingIx,
  createAtaIx,
  createVaultIx,
  fundVaultIx,
  listVaultIx,
  transferOwnershipIx,
  withdrawVestedIx,
} from "./instructions";
import { findAta, findListingPda } from "./pda";
import type {
  Cluster,
  ForgeParams,
  ForgeResult,
  Listing,
  ListingWithVault,
  SignerWallet,
  TxResult,
  Vault,
} from "./types";
import { isSignerWallet } from "./utils";

const LISTING_DISC_B58 = bs58.encode(LISTING_DISC);
const VAULT_DISC_B58 = bs58.encode(VAULT_DISC);

function explorer(sig: string, cluster: Cluster): string {
  return cluster === "mainnet-beta"
    ? `https://solscan.io/tx/${sig}`
    : `https://solscan.io/tx/${sig}?cluster=${cluster}`;
}

export class Client {
  private readonly connection: Connection;
  private readonly cluster: Cluster;

  private constructor(connection: Connection, cluster: Cluster) {
    this.connection = connection;
    this.cluster = cluster;
  }

  /** Create a client against the given RPC URL or a named cluster. */
  static connect(endpoint: string | Cluster = "devnet", commitment: Commitment = "confirmed"): Client {
    const url = endpoint === "devnet"
      ? DEVNET_RPC
      : endpoint === "mainnet-beta"
        ? "https://api.mainnet-beta.solana.com"
        : endpoint === "localnet"
          ? "http://127.0.0.1:8899"
          : endpoint;

    const cluster: Cluster =
      endpoint === "mainnet-beta" || endpoint === "localnet" || endpoint === "devnet"
        ? endpoint
        : url.includes("mainnet")
          ? "mainnet-beta"
          : url.includes("localhost") || url.includes("127.0.0.1")
            ? "localnet"
            : "devnet";
    return new Client(new Connection(url, commitment), cluster);
  }

  get rpc(): Connection {
    return this.connection;
  }

  /** Fetch and decode every active listing + its paired vault. */
  async fetchListings(): Promise<ListingWithVault[]> {
    const raw = await this.connection.getProgramAccounts(PROGRAM_ID, {
      filters: [
        { dataSize: LISTING_SIZE },
        { memcmp: { offset: 0, bytes: LISTING_DISC_B58 } },
      ],
    });

    const active: Listing[] = raw
      .map((acc) => decodeListing(acc.account.data, acc.pubkey))
      .filter((l): l is Listing => l.active);
    if (active.length === 0) return [];

    const vaultAccts = await this.connection.getMultipleAccountsInfo(
      active.map((l) => l.vault),
    );
    const out: ListingWithVault[] = [];
    for (let i = 0; i < active.length; i += 1) {
      const acct = vaultAccts[i];
      if (!acct) continue;
      const vault = decodeVault(acct.data, active[i].vault);
      out.push({ listing: active[i], vault });
    }
    // Newest first (vault_id is monotonic).
    out.sort((a, b) => Number(b.vault.vaultId - a.vault.vaultId));
    return out;
  }

  /** Fetch every vault owned by a given address. */
  async fetchMyCapsules(owner: PublicKey | string): Promise<{ vault: Vault; listing: Listing | null }[]> {
    const ownerKey = owner instanceof PublicKey ? owner : new PublicKey(owner);
    const raw = await this.connection.getProgramAccounts(PROGRAM_ID, {
      filters: [
        { dataSize: VAULT_SIZE },
        { memcmp: { offset: 0, bytes: VAULT_DISC_B58 } },
        { memcmp: { offset: 8, bytes: ownerKey.toBase58() } },
      ],
    });
    if (raw.length === 0) return [];
    const vaults = raw.map((r) => decodeVault(r.account.data, r.pubkey));
    const listingPdas = vaults.map((v) => findListingPda(v.pubkey));
    const listingAccts = await this.connection.getMultipleAccountsInfo(listingPdas);
    return vaults.map((v, i) => {
      const a = listingAccts[i];
      return {
        vault: v,
        listing: a ? decodeListing(a.data, listingPdas[i]) : null,
      };
    });
  }

  async fetchVault(pubkey: PublicKey | string): Promise<Vault> {
    const key = pubkey instanceof PublicKey ? pubkey : new PublicKey(pubkey);
    const info = await this.connection.getAccountInfo(key);
    if (!info) throw new VaultNotFoundError(key.toBase58());
    return decodeVault(info.data, key);
  }

  async fetchListing(pubkey: PublicKey | string): Promise<Listing> {
    const key = pubkey instanceof PublicKey ? pubkey : new PublicKey(pubkey);
    const info = await this.connection.getAccountInfo(key);
    if (!info) throw new ListingNotFoundError(key.toBase58());
    return decodeListing(info.data, key);
  }

  /** Forge: create + fund + list in a single tx. */
  async forge(params: ForgeParams): Promise<ForgeResult> {
    if (!isSignerWallet(params.wallet)) throw new WalletNotConnectedError();
    const wallet = params.wallet;
    const vestingMintKey = params.vestingMint instanceof PublicKey
      ? params.vestingMint
      : new PublicKey(params.vestingMint);
    const currencyMintKey = params.currencyMint
      ? (params.currencyMint instanceof PublicKey ? params.currencyMint : new PublicKey(params.currencyMint))
      : DEFAULT_DEVNET_CURRENCY;

    const vaultId = BigInt(Math.floor(Date.now() / 1000));

    const createIx = await createVaultIx({
      creator: wallet.publicKey,
      vestingMint: vestingMintKey,
      vaultId,
      totalAmount: BigInt(params.totalAmount),
      unlockStart: BigInt(params.unlockStart),
      unlockEnd: BigInt(params.unlockEnd),
    });

    const vault = createIx.keys[2].pubkey;
    const vaultTokenAccount = createIx.keys[3].pubkey;

    const fundIx = await fundVaultIx({
      funder: wallet.publicKey,
      vault,
      vestingMint: vestingMintKey,
      amount: BigInt(params.totalAmount),
    });

    const listIx = await listVaultIx({
      seller: wallet.publicKey,
      vault,
      currencyMint: currencyMintKey,
      price: BigInt(params.askingPrice),
    });
    const listing = listIx.keys[3].pubkey;

    const signature = await this.sendAndConfirm(wallet, [createIx, fundIx, listIx]);

    return {
      signature,
      vault: vault.toBase58(),
      vaultTokenAccount: vaultTokenAccount.toBase58(),
      listing: listing.toBase58(),
      explorer: explorer(signature, this.cluster),
    };
  }

  /** Acquire a listed vault at its current price. */
  async acquire(params: {
    wallet: SignerWallet;
    listing: Listing;
    vault: Vault;
  }): Promise<TxResult> {
    const { wallet, listing, vault } = params;
    if (!listing.active) throw new ListingInactiveError(listing.pubkey.toBase58());

    const buyerAta = findAta(wallet.publicKey, listing.currencyMint);
    const sellerAta = findAta(listing.seller, listing.currencyMint);

    const ixs = [];
    if (!(await this.connection.getAccountInfo(buyerAta))) {
      ixs.push(createAtaIx({ funder: wallet.publicKey, ata: buyerAta, owner: wallet.publicKey, mint: listing.currencyMint }));
    }
    if (!(await this.connection.getAccountInfo(sellerAta))) {
      ixs.push(createAtaIx({ funder: wallet.publicKey, ata: sellerAta, owner: listing.seller, mint: listing.currencyMint }));
    }
    ixs.push(await buyVaultIx({
      buyer: wallet.publicKey,
      seller: listing.seller,
      vault: vault.pubkey,
      listing: listing.pubkey,
      currencyMint: listing.currencyMint,
    }));

    const signature = await this.sendAndConfirm(wallet, ixs);
    return { signature, explorer: explorer(signature, this.cluster) };
  }

  /** Claim the currently-withdrawable thaw for a vault you own. */
  async claim(params: { wallet: SignerWallet; vault: Vault }): Promise<TxResult> {
    const { wallet, vault } = params;
    const ownerAta = findAta(wallet.publicKey, vault.vestingMint);

    const ixs = [];
    if (!(await this.connection.getAccountInfo(ownerAta))) {
      ixs.push(createAtaIx({ funder: wallet.publicKey, ata: ownerAta, owner: wallet.publicKey, mint: vault.vestingMint }));
    }
    ixs.push(await withdrawVestedIx({
      owner: wallet.publicKey,
      vault: vault.pubkey,
      vestingMint: vault.vestingMint,
    }));

    const signature = await this.sendAndConfirm(wallet, ixs);
    return { signature, explorer: explorer(signature, this.cluster) };
  }

  async cancelListing(params: { wallet: SignerWallet; listing: Listing }): Promise<TxResult> {
    const ix = await cancelListingIx({
      seller: params.wallet.publicKey,
      listing: params.listing.pubkey,
    });
    const signature = await this.sendAndConfirm(params.wallet, [ix]);
    return { signature, explorer: explorer(signature, this.cluster) };
  }

  async relist(params: {
    wallet: SignerWallet;
    vault: Vault;
    currencyMint: PublicKey | string;
    price: bigint | number | string;
  }): Promise<TxResult> {
    const currency = params.currencyMint instanceof PublicKey
      ? params.currencyMint
      : new PublicKey(params.currencyMint);
    const ix = await listVaultIx({
      seller: params.wallet.publicKey,
      vault: params.vault.pubkey,
      currencyMint: currency,
      price: BigInt(params.price),
    });
    const signature = await this.sendAndConfirm(params.wallet, [ix]);
    return { signature, explorer: explorer(signature, this.cluster) };
  }

  async transferOwnership(params: {
    wallet: SignerWallet;
    vault: Vault;
    newOwner: PublicKey | string;
  }): Promise<TxResult> {
    const newOwnerKey = params.newOwner instanceof PublicKey
      ? params.newOwner
      : new PublicKey(params.newOwner);
    const ix = await transferOwnershipIx({
      currentOwner: params.wallet.publicKey,
      newOwner: newOwnerKey,
      vault: params.vault.pubkey,
    });
    const signature = await this.sendAndConfirm(params.wallet, [ix]);
    return { signature, explorer: explorer(signature, this.cluster) };
  }

  /** Thin view helpers — no RPC round-trip. */
  thawed(vault: Vault, nowSec: bigint | number = Math.floor(Date.now() / 1000)): bigint {
    return computeThawed(vault, nowSec);
  }

  withdrawable(vault: Vault, nowSec: bigint | number = Math.floor(Date.now() / 1000)): bigint {
    return computeWithdrawable(vault, nowSec);
  }

  /* ---------------------------- internals ------------------------------ */

  private async sendAndConfirm(wallet: SignerWallet, ixs: any[]): Promise<string> {
    const { blockhash, lastValidBlockHeight } = await this.connection.getLatestBlockhash();
    const tx = new Transaction();
    for (const ix of ixs) tx.add(ix);
    tx.feePayer = wallet.publicKey;
    tx.recentBlockhash = blockhash;

    let signed: Transaction;
    try {
      signed = await wallet.signTransaction(tx);
    } catch (err: any) {
      throw new WalletSignatureError(err?.message || String(err));
    }

    const signature = await this.connection.sendRawTransaction(signed.serialize(), {
      preflightCommitment: "confirmed",
    });
    await this.connection.confirmTransaction(
      { signature, blockhash, lastValidBlockHeight },
      "confirmed",
    );
    return signature;
  }
}
