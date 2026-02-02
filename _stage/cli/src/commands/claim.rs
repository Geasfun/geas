use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;
use crate::util::parse_pubkey;

#[derive(Debug, Args)]
pub struct ClaimArgs {
    /// Vault pubkey to claim from.
    #[arg(long)]
    pub vault: String,
}

pub struct ClaimCmd;

impl ClaimCmd {
    pub fn run(ctx: &Context, args: ClaimArgs) -> Result<()> {
        let vault = parse_pubkey(&args.vault)?;
        info!(cluster = ctx.cluster_name(), %vault, "claim (dry-run)");
        println!("vault:    {}", vault);
        println!("cluster:  {}", ctx.cluster_name());
        println!();
        println!("If withdrawable > 0, submitting `withdraw_vested` will transfer the");
        println!("delta into your associated token account. Use the SDK to submit.");
        Ok(())
    }
}
