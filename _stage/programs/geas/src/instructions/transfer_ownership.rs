use anchor_lang::prelude::*;

use crate::constants::VAULT_SEED;
use crate::error::CryonicsError;
use crate::state::Vault;

#[derive(Accounts)]
pub struct TransferOwnership<'info> {
    #[account(mut)]
    pub current_owner: Signer<'info>,

    /// CHECK: new owner is any pubkey chosen by current owner
    pub new_owner: UncheckedAccount<'info>,

    #[account(
        mut,
        seeds = [VAULT_SEED, vault.creator.as_ref(), &vault.vault_id.to_le_bytes()],
        bump = vault.bump,
        constraint = vault.owner == current_owner.key() @ CryonicsError::NotOwner,
    )]
    pub vault: Account<'info, Vault>,
}

pub fn handler(ctx: Context<TransferOwnership>) -> Result<()> {
    let vault = &mut ctx.accounts.vault;
    vault.owner = ctx.accounts.new_owner.key();
    Ok(())
}
