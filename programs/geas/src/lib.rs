pub mod constants;
pub mod error;
pub mod instructions;
pub mod state;

use anchor_lang::prelude::*;

pub use constants::*;
pub use instructions::*;
pub use state::*;

declare_id!("CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53");

#[program]
pub mod geas {
    use super::*;

    pub fn create_vault(
        ctx: Context<CreateVault>,
        vault_id: u64,
        total_amount: u64,
        unlock_start: i64,
        unlock_end: i64,
    ) -> Result<()> {
        instructions::create_vault::handler(ctx, vault_id, total_amount, unlock_start, unlock_end)
    }

    pub fn fund_vault(ctx: Context<FundVault>, amount: u64) -> Result<()> {
        instructions::fund_vault::handler(ctx, amount)
    }

    pub fn list_vault(ctx: Context<ListVault>, price: u64) -> Result<()> {
        instructions::list_vault::handler(ctx, price)
    }

    pub fn cancel_listing(ctx: Context<CancelListing>) -> Result<()> {
        instructions::cancel_listing::handler(ctx)
    }

    pub fn buy_vault(ctx: Context<BuyVault>) -> Result<()> {
        instructions::buy_vault::handler(ctx)
    }

    pub fn transfer_ownership(ctx: Context<TransferOwnership>) -> Result<()> {
        instructions::transfer_ownership::handler(ctx)
    }

    pub fn withdraw_vested(ctx: Context<WithdrawVested>) -> Result<()> {
        instructions::withdraw_vested::handler(ctx)
    }
}
