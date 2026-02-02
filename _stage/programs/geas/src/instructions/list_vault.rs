use anchor_lang::prelude::*;
use anchor_spl::token::Mint;

use crate::constants::{LISTING_SEED, VAULT_SEED};
use crate::error::CryonicsError;
use crate::state::{Listing, Vault};

#[derive(Accounts)]
pub struct ListVault<'info> {
    #[account(mut)]
    pub seller: Signer<'info>,

    #[account(
        seeds = [VAULT_SEED, vault.creator.as_ref(), &vault.vault_id.to_le_bytes()],
        bump = vault.bump,
        constraint = vault.owner == seller.key() @ CryonicsError::NotOwner,
    )]
    pub vault: Account<'info, Vault>,

    pub currency_mint: Account<'info, Mint>,

    #[account(
        init,
        payer = seller,
        space = 8 + Listing::INIT_SPACE,
        seeds = [LISTING_SEED, vault.key().as_ref()],
        bump,
    )]
    pub listing: Account<'info, Listing>,

    pub system_program: Program<'info, System>,
}

pub fn handler(ctx: Context<ListVault>, price: u64) -> Result<()> {
    require!(price > 0, CryonicsError::InvalidAmount);

    let listing = &mut ctx.accounts.listing;
    listing.vault = ctx.accounts.vault.key();
    listing.seller = ctx.accounts.seller.key();
    listing.price = price;
    listing.currency_mint = ctx.accounts.currency_mint.key();
    listing.active = true;
    listing.bump = ctx.bumps.listing;

    Ok(())
}
