use anyhow::Result;
use clap::Args;
use tracing::info;

use crate::config::Context;
use crate::util::parse_pubkey;

#[derive(Debug, Args)]
pub struct InspectArgs {
    /// Account pubkey (vault or listing).
    #[arg(long)]
    pub pubkey: String,
}

pub struct InspectCmd;

impl InspectCmd {
    pub fn run(ctx: &Context, args: InspectArgs) -> Result<()> {
        let pk = parse_pubkey(&args.pubkey)?;
        info!(cluster = ctx.cluster_name(), %pk, "inspect");
        println!("pubkey:   {}", pk);
        println!("cluster:  {}", ctx.cluster_name());
        println!();
        println!("Account decoding requires the anchor borsh layout — pair this with");
        println!("`geas-cli listings` or the SDK's decodeVault / decodeListing helpers");
        println!("to pretty-print the payload.");
        Ok(())
    }
}
