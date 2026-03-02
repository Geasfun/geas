mod commands;
mod config;
mod error;
mod rpc;
mod util;

use anyhow::Result;
use clap::Parser;

use crate::commands::{
    AcquireCmd, CancelCmd, ClaimCmd, Command, ForgeCmd, InspectCmd, ListingsCmd, ThawPreviewCmd,
};

/// Top-level CLI entry point.
#[derive(Parser, Debug)]
#[command(
    name = "geas",
    bin_name = "geas-cli",
    version = env!("CARGO_PKG_VERSION"),
    about = "Command-line client for the geas program"
)]
struct Cli {
    /// Solana cluster name: localnet, devnet, mainnet-beta. Defaults to the
    /// GEAS_NETWORK environment variable, or "devnet".
    #[arg(long, global = true)]
    cluster: Option<String>,

    /// Path to a signer keypair (defaults to ~/.config/solana/id.json).
    #[arg(long, global = true)]
    keypair: Option<String>,

    #[command(subcommand)]
    command: Command,
}

fn init_logging() {
    let filter = std::env::var("GEAS_LOG_LEVEL").unwrap_or_else(|_| "info".to_string());
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::new(filter))
        .with_target(false)
        .compact()
        .init();
}

fn main() -> Result<()> {
    init_logging();
    let cli = Cli::parse();
    let ctx = config::Context::from_flags(cli.cluster.as_deref(), cli.keypair.as_deref())?;

    match cli.command {
        Command::Forge(cmd) => ForgeCmd::run(&ctx, cmd),
        Command::Acquire(cmd) => AcquireCmd::run(&ctx, cmd),
        Command::Claim(cmd) => ClaimCmd::run(&ctx, cmd),
        Command::Cancel(cmd) => CancelCmd::run(&ctx, cmd),
        Command::Inspect(cmd) => InspectCmd::run(&ctx, cmd),
        Command::Listings(cmd) => ListingsCmd::run(&ctx, cmd),
        Command::ThawPreview(cmd) => ThawPreviewCmd::run(&ctx, cmd),
    }
}
