use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount, Transfer};

use crate::constants::{VAULT_SEED, VAULT_TA_SEED};
use crate::error::CryonicsError;
use crate::state::Vault;

#[derive(Accounts)]
pub struct WithdrawVested<'info> {
    #[account(mut)]
    pub owner: Signer<'info>,

    #[account(
        mut,
        seeds = [VAULT_SEED, vault.creator.as_ref(), &vault.vault_id.to_le_bytes()],
        bump = vault.bump,
        has_one = vesting_mint,
        constraint = vault.owner == owner.key() @ CryonicsError::NotOwner,
    )]
    pub vault: Account<'info, Vault>,

    pub vesting_mint: Account<'info, Mint>,

    #[account(
        mut,
        seeds = [VAULT_TA_SEED, vault.key().as_ref()],
        bump = vault.token_account_bump,
    )]
    pub vault_token_account: Account<'info, TokenAccount>,

    #[account(
        mut,
        token::mint = vesting_mint,
        token::authority = owner,
    )]
    pub owner_token_account: Account<'info, TokenAccount>,

    pub token_program: Program<'info, Token>,
}

pub fn handler(ctx: Context<WithdrawVested>) -> Result<()> {
    let clock = Clock::get()?;
    let claimable = ctx.accounts.vault.claimable(clock.unix_timestamp);
    require!(claimable > 0, CryonicsError::NothingClaimable);

    let vault_ta_balance = ctx.accounts.vault_token_account.amount;
    let to_transfer = claimable.min(vault_ta_balance);
    require!(to_transfer > 0, CryonicsError::NothingClaimable);

    let creator = ctx.accounts.vault.creator;
    let vault_id_bytes = ctx.accounts.vault.vault_id.to_le_bytes();
    let vault_bump = ctx.accounts.vault.bump;

    let vault_seeds: &[&[u8]] = &[
        VAULT_SEED,
        creator.as_ref(),
        &vault_id_bytes,
        core::slice::from_ref(&vault_bump),
    ];
    let signer_seeds = &[vault_seeds];

    let cpi_ctx = CpiContext::new_with_signer(
        *ctx.accounts.token_program.key,
        Transfer {
            from: ctx.accounts.vault_token_account.to_account_info(),
            to: ctx.accounts.owner_token_account.to_account_info(),
            authority: ctx.accounts.vault.to_account_info(),
        },
        signer_seeds,
    );
    token::transfer(cpi_ctx, to_transfer)?;

    let vault = &mut ctx.accounts.vault;
    vault.claimed_amount = vault
        .claimed_amount
        .checked_add(to_transfer)
        .ok_or(CryonicsError::MathOverflow)?;

    Ok(())
}
