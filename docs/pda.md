# PDA derivation

All PDAs in geas use explicit, self-describing seeds. The program ID is
`CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53`.

| PDA                | Seeds                                         |
| ------------------ | --------------------------------------------- |
| Vault              | `[b"vault", creator, vault_id_u64_le]`        |
| Vault token account| `[b"vault-ta", vault]`                        |
| Listing            | `[b"listing", vault]`                         |

## `vault_id`

The creator chooses a `u64` at `create_vault` time. The SDK defaults to
`Math.floor(Date.now() / 1000)` so two capsules from the same creator can't
collide unless they are forged in the exact same second. `vault_id` is part of
the vault seed so `(creator, vault_id)` uniquely identifies a vault.

## Rust derivation

```rust
let (vault, bump) = Pubkey::find_program_address(
    &[b"vault", creator.as_ref(), &vault_id.to_le_bytes()],
    &program_id,
);
```

## TypeScript derivation

```ts
const [vault] = PublicKey.findProgramAddressSync(
  [Buffer.from("vault"), creator.toBuffer(), u64LE(vaultId)],
  PROGRAM_ID,
);
```

## Why include creator in the seed?

It lets anyone's address be a creator without seed collisions between users,
and lets existing off-chain indexers key on the creator for range scans.
