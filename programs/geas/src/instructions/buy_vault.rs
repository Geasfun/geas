use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount, Transfer};

use crate::constants::{LISTING_SEED, VAULT_SEED};
use crate::error::CryonicsError;
use crate::state::{Listing, Vault};

#[derive(Accounts)]
pub struct BuyVault<'info> {
    #[account(mut)]
    pub buyer: Signer<'info>,

    /// CHECK: Seller pubkey is validated against listing.seller.
    #[account(mut, address = listing.seller @ CryonicsError::NotSeller)]
    pub seller: UncheckedAccount<'info>,

    #[account(
        mut,
        seeds = [VAULT_SEED, vault.creator.as_ref(), &vault.vault_id.to_le_bytes()],
        bump = vault.bump,
    )]
    pub vault: Account<'info, Vault>,

    #[account(
        mut,
        seeds = [LISTING_SEED, vault.key().as_ref()],
        bump = listing.bump,
        close = seller,
        has_one = vault,
        constraint = listing.active @ CryonicsError::ListingInactive,
    )]
    pub listing: Account<'info, Listing>,

    #[account(address = listing.currency_mint)]
    pub currency_mint: Account<'info, Mint>,

    #[account(
        mut,
        token::mint = currency_mint,
        token::authority = buyer,
    )]
    pub buyer_currency_account: Account<'info, TokenAccount>,

    #[account(
        mut,
        token::mint = currency_mint,
    )]
    pub seller_currency_account: Account<'info, TokenAccount>,

    pub token_program: Program<'info, Token>,
}

pub fn handler(ctx: Context<BuyVault>) -> Result<()> {
    let price = ctx.accounts.listing.price;

    let cpi_ctx = CpiContext::new(
        *ctx.accounts.token_program.key,
        Transfer {
            from: ctx.accounts.buyer_currency_account.to_account_info(),
            to: ctx.accounts.seller_currency_account.to_account_info(),
            authority: ctx.accounts.buyer.to_account_info(),
        },
    );
    token::transfer(cpi_ctx, price)?;

    // Transfer vault ownership to buyer
    let vault = &mut ctx.accounts.vault;
    vault.owner = ctx.accounts.buyer.key();

    Ok(())
}
