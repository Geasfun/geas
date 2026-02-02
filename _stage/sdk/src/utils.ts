import { PublicKey } from "@solana/web3.js";

/** Concatenate several byte arrays into one. */
export function concatBytes(...arrays: Uint8Array[]): Uint8Array {
  const total = arrays.reduce((sum, arr) => sum + arr.length, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const arr of arrays) {
    out.set(arr, offset);
    offset += arr.length;
  }
  return out;
}

export function u64LE(value: bigint | number | string): Uint8Array {
  const buf = new Uint8Array(8);
  new DataView(buf.buffer).setBigUint64(0, BigInt(value), true);
  return buf;
}

export function i64LE(value: bigint | number | string): Uint8Array {
  const buf = new Uint8Array(8);
  new DataView(buf.buffer).setBigInt64(0, BigInt(value), true);
  return buf;
}

export function readU64LE(buf: Uint8Array, off: number): bigint {
  return new DataView(buf.buffer, buf.byteOffset, buf.byteLength).getBigUint64(off, true);
}

export function readI64LE(buf: Uint8Array, off: number): bigint {
  return new DataView(buf.buffer, buf.byteOffset, buf.byteLength).getBigInt64(off, true);
}

export function readPubkey(buf: Uint8Array, off: number): PublicKey {
  return new PublicKey(buf.slice(off, off + 32));
}

/** Pretty print a pubkey: `4k3D…aAfQ`. */
export function shortAddr(pk: PublicKey | string, head = 4, tail = 4): string {
  const s = typeof pk === "string" ? pk : pk.toBase58();
  return s.length > head + tail + 1 ? `${s.slice(0, head)}…${s.slice(-tail)}` : s;
}

/** Compute the Anchor instruction discriminator for a given snake_case name. */
export async function discriminator(ixName: string): Promise<Uint8Array> {
  const data = new TextEncoder().encode(`global:${ixName}`);
  const hash = new Uint8Array(await crypto.subtle.digest("SHA-256", data));
  return hash.slice(0, 8);
}

/** Divide bigints, rounding toward zero (matches Rust's integer division). */
export function divTruncate(num: bigint, denom: bigint): bigint {
  if (denom === 0n) throw new Error("division by zero");
  return num / denom;
}

/** Clamp a bigint into the inclusive range [lo, hi]. */
export function clampBigInt(value: bigint, lo: bigint, hi: bigint): bigint {
  if (value < lo) return lo;
  if (value > hi) return hi;
  return value;
}

/** True if `obj` exposes both `publicKey` and `signTransaction`. */
export function isSignerWallet(obj: unknown): boolean {
  if (!obj || typeof obj !== "object") return false;
  const candidate = obj as { publicKey?: unknown; signTransaction?: unknown };
  return Boolean(candidate.publicKey) && typeof candidate.signTransaction === "function";
}
