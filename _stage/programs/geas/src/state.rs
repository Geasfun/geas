use anchor_lang::prelude::*;

#[account]
#[derive(InitSpace)]
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

impl Vault {
    pub fn vested_amount(&self, now: i64) -> u64 {
        if now <= self.unlock_start {
            return 0;
        }
        if now >= self.unlock_end {
            return self.total_amount;
        }
        let elapsed = (now - self.unlock_start) as u128;
        let duration = (self.unlock_end - self.unlock_start) as u128;
        let vested = (self.total_amount as u128)
            .checked_mul(elapsed)
            .unwrap()
            .checked_div(duration)
            .unwrap();
        vested as u64
    }

    pub fn claimable(&self, now: i64) -> u64 {
        self.vested_amount(now).saturating_sub(self.claimed_amount)
    }
}

#[account]
#[derive(InitSpace)]
pub struct Listing {
    pub vault: Pubkey,
    pub seller: Pubkey,
    pub price: u64,
    pub currency_mint: Pubkey,
    pub active: bool,
    pub bump: u8,
}
