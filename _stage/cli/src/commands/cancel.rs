use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;
use crate::util::parse_pubkey;

#[derive(Debug, Args)]
pub struct CancelArgs {
    /// Listing pubkey to cancel.
    #[arg(long)]
    pub listing: String,
}

pub struct CancelCmd;

impl CancelCmd {
    pub fn run(ctx: &Context, args: CancelArgs) -> Result<()> {
        let listing = parse_pubkey(&args.listing)?;
        info!(cluster = ctx.cluster_name(), %listing, "cancel (dry-run)");
        println!("listing:  {}", listing);
        println!("cluster:  {}", ctx.cluster_name());
        Ok(())
    }
}
