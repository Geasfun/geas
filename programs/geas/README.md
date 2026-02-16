# geas program

On-chain Anchor program. Seven instructions that let a vesting holder mint a
transferable capsule and a buyer acquire it at a discount, with the unlock
schedule carrying over to the new owner.

## Instructions

| Name                | Args                                                      | Notes                                   |
| ------------------- | --------------------------------------------------------- | --------------------------------------- |
| `create_vault`      | `vault_id`, `total_amount`, `unlock_start`, `unlock_end`  | Allocates the vault PDA + token PDA     |
| `fund_vault`        | `amount`                                                  | Moves locked tokens into the vault TA   |
| `list_vault`        | `price`                                                   | Creates a `Listing` PDA                 |
| `cancel_listing`    | —                                                         | Closes the `Listing`, refunds rent      |
| `buy_vault`         | —                                                         | Pays the seller, swaps ownership        |
| `transfer_ownership`| —                                                         | Direct owner-to-owner transfer          |
| `withdraw_vested`   | —                                                         | Pays `thawed − claimed` to the owner    |

## PDA seeds

| PDA                  | Seeds                                        |
| -------------------- | -------------------------------------------- |
| Vault                | `["vault", creator, vault_id]`               |
| Vault token account  | `["vault-ta", vault]`                        |
| Listing              | `["listing", vault]`                         |

## State

```rust
pub struct Vault {
    pub owner: Pubkey,
    pub creator: Pubkey,
    pub vesting_mint: Pubkey,
    pub total_amount: u64,
    pub claimed_amount: u64,
    pub unlock_start: i64,
    pub unlock_end: i64,
    pub vault_id: u64,
    pub bump: u8,
    pub token_account_bump: u8,
}

pub struct Listing {
    pub vault: Pubkey,
    pub seller: Pubkey,
    pub price: u64,
    pub currency_mint: Pubkey,
    pub active: bool,
    pub bump: u8,
}
```

## Unlock curve

Linear thaw between `unlock_start` and `unlock_end`, saturating at
`total_amount` after the end:

    thawed(t) = total * max(0, min(1, (t − start) / (end − start)))
    withdrawable = thawed(t) − claimed_amount

All math is integer-only; truncation is intentional and matches on-chain rounding.

## Build

```
anchor build
```

The resulting shared object lands at `target/deploy/geas.so` and the IDL at
`target/idl/geas.json`.
