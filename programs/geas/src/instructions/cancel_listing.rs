use anchor_lang::prelude::*;

use crate::constants::LISTING_SEED;
use crate::error::CryonicsError;
use crate::state::Listing;

#[derive(Accounts)]
pub struct CancelListing<'info> {
    #[account(mut)]
    pub seller: Signer<'info>,

    #[account(
        mut,
        seeds = [LISTING_SEED, listing.vault.as_ref()],
        bump = listing.bump,
        close = seller,
        constraint = listing.seller == seller.key() @ CryonicsError::NotSeller,
        constraint = listing.active @ CryonicsError::ListingInactive,
    )]
    pub listing: Account<'info, Listing>,
}

pub fn handler(_ctx: Context<CancelListing>) -> Result<()> {
    // Listing account is closed by the account constraint (rent refunded to seller).
    Ok(())
}
