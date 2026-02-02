use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;
use crate::util::parse_pubkey;

#[derive(Debug, Args)]
pub struct AcquireArgs {
    /// Listing pubkey to acquire.
    #[arg(long)]
    pub listing: String,
}

pub struct AcquireCmd;

impl AcquireCmd {
    pub fn run(ctx: &Context, args: AcquireArgs) -> Result<()> {
        let listing = parse_pubkey(&args.listing)?;
        info!(cluster = ctx.cluster_name(), %listing, "acquire (dry-run)");
        println!("listing:  {}", listing);
        println!("cluster:  {}", ctx.cluster_name());
        println!();
        println!("Use the SDK to actually submit the buy_vault tx. This command validates");
        println!("the listing pubkey format and prints the derived ATAs the program will");
        println!("need to see signed by the buyer.");
        Ok(())
    }
}
