use anyhow::Result;
use solana_program::pubkey::Pubkey;

use crate::error::CliError;

/// geas program id.
pub const PROGRAM_ID_STR: &str = "CuoDH7XTZSqon2WhR2uixNsYrFkFRzRKgxDfra5vih53";
pub const TOKEN_PROGRAM_ID_STR: &str = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
pub const ASSOC_TOKEN_PROGRAM_ID_STR: &str = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL";

pub fn program_id() -> Pubkey {
    PROGRAM_ID_STR.parse().expect("valid program id")
}

pub fn token_program_id() -> Pubkey {
    TOKEN_PROGRAM_ID_STR.parse().expect("valid token program id")
}

pub fn assoc_token_program_id() -> Pubkey {
    ASSOC_TOKEN_PROGRAM_ID_STR
        .parse()
        .expect("valid ATA program id")
}

/// Parse a base58 public key, returning a CLI-friendly error.
pub fn parse_pubkey(s: &str) -> Result<Pubkey, CliError> {
    s.parse::<Pubkey>()
        .map_err(|_| CliError::InvalidPubkey(s.to_string()))
}

/// Parse a timestamp in either RFC3339 or raw unix seconds.
pub fn parse_timestamp(s: &str) -> Result<i64, CliError> {
    if let Ok(epoch) = s.parse::<i64>() {
        return Ok(epoch);
    }
    // Minimal RFC3339 parser: accept `YYYY-MM-DDTHH:MM:SSZ`.
    let normalized = s.replace('z', "Z");
    let without_tz = normalized.trim_end_matches('Z');
    let parts: Vec<&str> = without_tz.split('T').collect();
    if parts.len() != 2 {
        return Err(CliError::InvalidTimestamp(s.to_string()));
    }
    let date: Vec<&str> = parts[0].split('-').collect();
    let time: Vec<&str> = parts[1].split(':').collect();
    if date.len() != 3 || time.len() != 3 {
        return Err(CliError::InvalidTimestamp(s.to_string()));
    }
    let year: i64 = date[0].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;
    let month: u32 = date[1].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;
    let day: u32 = date[2].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;
    let hour: u32 = time[0].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;
    let minute: u32 = time[1].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;
    let second: u32 = time[2].parse().map_err(|_| CliError::InvalidTimestamp(s.to_string()))?;

    Ok(days_from_civil(year, month, day) * 86_400
        + (hour as i64) * 3_600
        + (minute as i64) * 60
        + (second as i64))
}

/// Howard Hinnant's civil-from-days algorithm, inverted.
/// Returns the number of days since 1970-01-01 for the given Y/M/D.
fn days_from_civil(y: i64, m: u32, d: u32) -> i64 {
    let y = if m <= 2 { y - 1 } else { y };
    let era = if y >= 0 { y } else { y - 399 } / 400;
    let yoe = (y - era * 400) as i64;
    let doy = (153 * (if m > 2 { m - 3 } else { m + 9 }) as i64 + 2) / 5 + (d as i64) - 1;
    let doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    era * 146_097 + doe - 719_468
}

pub fn parse_amount(s: &str) -> Result<u64, CliError> {
    s.replace(['_', ','], "")
        .parse::<u64>()
        .map_err(|_| CliError::InvalidAmount(s.to_string()))
}

/// Compute thawed amount client-side, matching on-chain integer math.
pub fn compute_thawed(total: u64, _claimed: u64, unlock_start: i64, unlock_end: i64, now: i64) -> u64 {
    if now <= unlock_start {
        return 0;
    }
    if now >= unlock_end {
        return total;
    }
    let span = (unlock_end - unlock_start) as u128;
    let elapsed = (now - unlock_start) as u128;
    let thawed = ((total as u128) * elapsed) / span;
    thawed.min(u64::MAX as u128) as u64
}
