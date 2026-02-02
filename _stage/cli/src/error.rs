use thiserror::Error;

#[derive(Debug, Error)]
pub enum CliError {
    #[error("unknown cluster `{0}` — expected one of: localnet, devnet, mainnet-beta")]
    UnknownCluster(String),

    #[error("failed to read keypair from {path}: {source}")]
    KeypairRead {
        path: String,
        source: std::io::Error,
    },

    #[error("could not locate a default solana home directory")]
    MissingHomeDir,

    #[error("invalid pubkey `{0}`")]
    InvalidPubkey(String),

    #[error("invalid timestamp `{0}` — use RFC3339 (2026-01-01T00:00:00Z) or unix seconds")]
    InvalidTimestamp(String),

    #[error("invalid amount `{0}` — must be a non-negative integer")]
    InvalidAmount(String),

    #[error("no listing found at {0}")]
    ListingNotFound(String),

    #[error("no vault found at {0}")]
    VaultNotFound(String),

    #[error("listing {0} is inactive")]
    ListingInactive(String),
}

pub type CliResult<T> = Result<T, CliError>;
