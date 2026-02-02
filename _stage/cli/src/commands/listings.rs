use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;

#[derive(Debug, Args)]
pub struct ListingsArgs {
    /// Optional filter: only show listings with a price <= this value.
    #[arg(long)]
    pub max_price: Option<u64>,

    /// Optional filter: only show listings on this currency mint.
    #[arg(long)]
    pub currency_mint: Option<String>,
}

pub struct ListingsCmd;

impl ListingsCmd {
    pub fn run(ctx: &Context, args: ListingsArgs) -> Result<()> {
        info!(
            cluster = ctx.cluster_name(),
            max_price = ?args.max_price,
            currency_mint = ?args.currency_mint,
            "listings (stub, dry-run)"
        );
        println!("cluster:      {}", ctx.cluster_name());
        println!("max_price:    {:?}", args.max_price);
        println!("currency:     {:?}", args.currency_mint);
        println!();
        println!("This subcommand is a plan-only wrapper — run the SDK's fetchListings");
        println!("for a live RPC query.");
        Ok(())
    }
}
