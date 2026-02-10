use anchor_lang::prelude::*;

#[error_code]
pub enum CryonicsError {
    #[msg("Unlock end must be strictly greater than unlock start")]
    InvalidSchedule,
    #[msg("Total amount must be greater than zero")]
    InvalidAmount,
    #[msg("Caller is not the current vault owner")]
    NotOwner,
    #[msg("Caller is not the listing seller")]
    NotSeller,
    #[msg("Listing is not active")]
    ListingInactive,
    #[msg("Nothing vested is currently claimable")]
    NothingClaimable,
    #[msg("Math overflow")]
    MathOverflow,
    #[msg("Vault is still funded; withdraw before closing")]
    VaultNotEmpty,
    #[msg("Cannot list vault while listing is already active")]
    ListingAlreadyActive,
}
