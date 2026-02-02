import {
  clampBigInt,
  concatBytes,
  divTruncate,
  i64LE,
  readI64LE,
  readU64LE,
  shortAddr,
  u64LE,
} from "../src/utils";

describe("byte helpers", () => {
  it("u64LE round-trips", () => {
    const buf = u64LE(42n);
    expect(readU64LE(buf, 0)).toEqual(42n);
  });

  it("i64LE supports negative values", () => {
    const buf = i64LE(-1n);
    expect(readI64LE(buf, 0)).toEqual(-1n);
  });

  it("concatBytes lays buffers end-to-end", () => {
    const out = concatBytes(new Uint8Array([1, 2]), new Uint8Array([3, 4]));
    expect(Array.from(out)).toEqual([1, 2, 3, 4]);
  });

  it("shortAddr truncates long strings", () => {
    expect(shortAddr("11111111111111111111111111111111")).toEqual("1111…1111");
  });

  it("divTruncate rounds toward zero for negative numerators", () => {
    expect(divTruncate(-7n, 2n)).toEqual(-3n);
  });

  it("clampBigInt respects bounds", () => {
    expect(clampBigInt(5n, 0n, 10n)).toEqual(5n);
    expect(clampBigInt(-1n, 0n, 10n)).toEqual(0n);
    expect(clampBigInt(11n, 0n, 10n)).toEqual(10n);
  });
});
