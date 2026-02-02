/**
 * Strongly-typed errors thrown by the SDK. The program itself has additional
 * codes raised through Anchor; those surface as `SendTransactionError` from
 * web3.js and should be caught at the call site.
 */
export class SdkError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "SdkError";
    this.code = code;
  }
}

export class WalletNotConnectedError extends SdkError {
  constructor() {
    super("WALLET_NOT_CONNECTED", "Wallet does not expose a publicKey");
  }
}

export class WalletSignatureError extends SdkError {
  constructor(reason: string) {
    super("WALLET_SIGNATURE", `Wallet signTransaction rejected or failed: ${reason}`);
  }
}

export class AccountDecodeError extends SdkError {
  constructor(kind: "Vault" | "Listing", reason: string) {
    super("ACCOUNT_DECODE", `${kind} decode failed: ${reason}`);
  }
}

export class ListingNotFoundError extends SdkError {
  constructor(pubkey: string) {
    super("LISTING_NOT_FOUND", `Listing ${pubkey} was not found on-chain`);
  }
}

export class VaultNotFoundError extends SdkError {
  constructor(pubkey: string) {
    super("VAULT_NOT_FOUND", `Vault ${pubkey} was not found on-chain`);
  }
}

export class ListingInactiveError extends SdkError {
  constructor(pubkey: string) {
    super("LISTING_INACTIVE", `Listing ${pubkey} is no longer active`);
  }
}

export class InvariantBrokenError extends SdkError {
  constructor(field: string, detail: string) {
    super("INVARIANT_BROKEN", `invariant on ${field} violated: ${detail}`);
  }
}
