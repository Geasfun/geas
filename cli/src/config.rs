use std::path::PathBuf;

use anyhow::{Context as AnyhowContext, Result};
use solana_sdk::signature::{Keypair, read_keypair_file};

use crate::error::CliError;

/// Runtime configuration derived from CLI flags + environment variables.
#[derive(Debug, Clone)]
pub struct Context {
    pub cluster: Cluster,
    pub keypair_path: PathBuf,
    pub rpc_url: String,
    pub ws_url: String,
}

/// Supported Solana clusters. We deliberately don't expose a "custom" variant
/// from the CLI — pass `--cluster <url>` indirectly via `GEAS_RPC_URL`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Cluster {
    Localnet,
    Devnet,
    MainnetBeta,
}

impl Cluster {
    pub fn from_flag(raw: &str) -> Result<Self, CliError> {
        match raw.to_ascii_lowercase().as_str() {
            "localnet" | "local" => Ok(Cluster::Localnet),
            "devnet" => Ok(Cluster::Devnet),
            "mainnet-beta" | "mainnet" => Ok(Cluster::MainnetBeta),
            other => Err(CliError::UnknownCluster(other.to_string())),
        }
    }

    pub fn rpc_url(self) -> &'static str {
        match self {
            Cluster::Localnet => "http://127.0.0.1:8899",
            Cluster::Devnet => "https://api.devnet.solana.com",
            Cluster::MainnetBeta => "https://api.mainnet-beta.solana.com",
        }
    }

    pub fn ws_url(self) -> &'static str {
        match self {
            Cluster::Localnet => "ws://127.0.0.1:8900",
            Cluster::Devnet => "wss://api.devnet.solana.com",
            Cluster::MainnetBeta => "wss://api.mainnet-beta.solana.com",
        }
    }
}

impl Context {
    pub fn from_flags(cluster_flag: Option<&str>, keypair_flag: Option<&str>) -> Result<Self> {
        let cluster_raw = cluster_flag
            .map(str::to_string)
            .or_else(|| std::env::var("GEAS_NETWORK").ok())
            .unwrap_or_else(|| "devnet".to_string());
        let cluster = Cluster::from_flag(&cluster_raw)?;

        let rpc_url = std::env::var("GEAS_RPC_URL")
            .unwrap_or_else(|_| cluster.rpc_url().to_string());
        let ws_url = std::env::var("GEAS_WS_URL")
            .unwrap_or_else(|_| cluster.ws_url().to_string());

        let keypair_path = if let Some(explicit) = keypair_flag {
            PathBuf::from(explicit)
        } else if let Ok(env_path) = std::env::var("GEAS_KEYPAIR_PATH") {
            expand_tilde(&env_path)?
        } else {
            default_keypair_path()?
        };

        Ok(Self {
            cluster,
            keypair_path,
            rpc_url,
            ws_url,
        })
    }

    pub fn load_keypair(&self) -> Result<Keypair> {
        read_keypair_file(&self.keypair_path).map_err(|e| {
            CliError::KeypairRead {
                path: self.keypair_path.display().to_string(),
                source: std::io::Error::new(std::io::ErrorKind::Other, e.to_string()),
            }
            .into()
        })
    }

    pub fn cluster_name(&self) -> &'static str {
        match self.cluster {
            Cluster::Localnet => "localnet",
            Cluster::Devnet => "devnet",
            Cluster::MainnetBeta => "mainnet-beta",
        }
    }
}

fn default_keypair_path() -> Result<PathBuf> {
    let home = dirs::home_dir().ok_or(CliError::MissingHomeDir)?;
    Ok(home.join(".config").join("solana").join("id.json"))
}

fn expand_tilde(path: &str) -> Result<PathBuf> {
    if let Some(stripped) = path.strip_prefix("~/") {
        let home = dirs::home_dir().ok_or(CliError::MissingHomeDir)?;
        Ok(home.join(stripped))
    } else {
        Ok(PathBuf::from(path))
    }
}
