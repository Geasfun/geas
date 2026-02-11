use anchor_lang::prelude::*;
use anchor_spl::token::{Mint, Token, TokenAccount};

use crate::constants::{VAULT_SEED, VAULT_TA_SEED};
use crate::error::CryonicsError;
use crate::state::Vault;

#[derive(Accounts)]
#[instruction(vault_id: u64)]
pub struct CreateVault<'info> {
    #[account(mut)]
    pub creator: Signer<'info>,

    pub vesting_mint: Account<'info, Mint>,

    #[account(
        init,
        payer = creator,
        space = 8 + Vault::INIT_SPACE,
        seeds = [VAULT_SEED, creator.key().as_ref(), &vault_id.to_le_bytes()],
        bump,
    )]
    pub vault: Account<'info, Vault>,

    #[account(
        init,
        payer = creator,
        seeds = [VAULT_TA_SEED, vault.key().as_ref()],
        bump,
        token::mint = vesting_mint,
        token::authority = vault,
    )]
    pub vault_token_account: Account<'info, TokenAccount>,

    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub rent: Sysvar<'info, Rent>,
}

pub fn handler(
    ctx: Context<CreateVault>,
    vault_id: u64,
    total_amount: u64,
    unlock_start: i64,
    unlock_end: i64,
) -> Result<()> {
    require!(unlock_end > unlock_start, CryonicsError::InvalidSchedule);
    require!(total_amount > 0, CryonicsError::InvalidAmount);

    let vault = &mut ctx.accounts.vault;
    vault.owner = ctx.accounts.creator.key();
    vault.creator = ctx.accounts.creator.key();
    vault.vesting_mint = ctx.accounts.vesting_mint.key();
    vault.total_amount = total_amount;
    vault.claimed_amount = 0;
    vault.unlock_start = unlock_start;
    vault.unlock_end = unlock_end;
    vault.vault_id = vault_id;
    vault.bump = ctx.bumps.vault;
    vault.token_account_bump = ctx.bumps.vault_token_account;

    Ok(())
}
