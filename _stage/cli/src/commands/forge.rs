use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;
use crate::util::{parse_amount, parse_pubkey, parse_timestamp};

#[derive(Debug, Args)]
pub struct ForgeArgs {
    /// SPL mint of the vesting token.
    #[arg(long)]
    pub vesting_mint: String,

    /// Raw u64 amount of tokens to lock.
    #[arg(long)]
    pub amount: String,

    /// Unlock start (RFC3339 or unix seconds).
    #[arg(long)]
    pub unlock_start: String,

    /// Unlock end (RFC3339 or unix seconds).
    #[arg(long)]
    pub unlock_end: String,

    /// Asking price in the currency mint's smallest units.
    #[arg(long)]
    pub price: String,

    /// Currency mint (defaults to devnet USDC).
    #[arg(long, default_value = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")]
    pub currency_mint: String,

    /// Decimals of the vesting token (informational only, not sent on-chain).
    #[arg(long, default_value_t = 6)]
    pub decimals: u8,
}

pub struct ForgeCmd;

impl ForgeCmd {
    pub fn run(ctx: &Context, args: ForgeArgs) -> Result<()> {
        let vesting_mint = parse_pubkey(&args.vesting_mint)?;
        let currency_mint = parse_pubkey(&args.currency_mint)?;
        let amount = parse_amount(&args.amount)?;
        let price = parse_amount(&args.price)?;
        let start = parse_timestamp(&args.unlock_start)?;
        let end = parse_timestamp(&args.unlock_end)?;

        if end <= start {
            anyhow::bail!("unlock_end must be strictly greater than unlock_start");
        }

        info!(
            cluster = ctx.cluster_name(),
            vesting_mint = %vesting_mint,
            currency_mint = %currency_mint,
            amount,
            price,
            unlock_start = start,
            unlock_end = end,
            decimals = args.decimals,
            "forging capsule (dry-run)"
        );

        println!("vesting mint:   {}", vesting_mint);
        println!("currency mint:  {}", currency_mint);
        println!("amount:         {}", amount);
        println!("asking price:   {}", price);
        println!("unlock window:  {} -> {}", start, end);
        println!();
        println!("The CLI prints a deterministic plan. To actually submit, pair this");
        println!("command with the TypeScript SDK or a web3.js harness under the same");
        println!("key. Forge-from-CLI is dry-run for now — it lets you confirm inputs");
        println!("before pressing the network button.");

        Ok(())
    }
}
