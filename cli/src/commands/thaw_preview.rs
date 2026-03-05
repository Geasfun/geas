use anyhow::Result;
use clap::Args;

use crate::config::Context;
use crate::util::{compute_thawed, parse_amount, parse_timestamp};

#[derive(Debug, Args)]
pub struct ThawPreviewArgs {
    /// Total vesting amount (raw u64).
    #[arg(long)]
    pub total: String,

    /// Already-claimed amount (raw u64).
    #[arg(long, default_value = "0")]
    pub claimed: String,

    /// Unlock start (RFC3339 or unix seconds).
    #[arg(long)]
    pub unlock_start: String,

    /// Unlock end (RFC3339 or unix seconds).
    #[arg(long)]
    pub unlock_end: String,

    /// Timestamp to preview at (default: now).
    #[arg(long)]
    pub at: Option<String>,
}

pub struct ThawPreviewCmd;

impl ThawPreviewCmd {
    pub fn run(_ctx: &Context, args: ThawPreviewArgs) -> Result<()> {
        let total = parse_amount(&args.total)?;
        let claimed = parse_amount(&args.claimed)?;
        let start = parse_timestamp(&args.unlock_start)?;
        let end = parse_timestamp(&args.unlock_end)?;
        let now = match args.at.as_deref() {
            Some(s) => parse_timestamp(s)?,
            None => std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map(|d| d.as_secs() as i64)
                .unwrap_or(0),
        };
        let thawed = compute_thawed(total, claimed, start, end, now);
        let withdrawable = thawed.saturating_sub(claimed);

        println!("total:         {}", total);
        println!("claimed:       {}", claimed);
        println!("unlock_start:  {}", start);
        println!("unlock_end:    {}", end);
        println!("at:            {}", now);
        println!();
        println!("thawed:        {}", thawed);
        println!("withdrawable:  {}", withdrawable);

        Ok(())
    }
}
