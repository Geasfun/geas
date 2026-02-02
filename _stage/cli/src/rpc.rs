use anyhow::Result;
use solana_client::rpc_client::RpcClient;
use solana_sdk::commitment_config::CommitmentConfig;

use crate::config::Context;

pub fn make_client(ctx: &Context) -> Result<RpcClient> {
    Ok(RpcClient::new_with_commitment(
        ctx.rpc_url.clone(),
        CommitmentConfig::confirmed(),
    ))
}
