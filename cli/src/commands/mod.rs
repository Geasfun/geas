mod acquire;
mod cancel;
mod claim;
mod forge;
mod inspect;
mod listings;
mod thaw_preview;

pub use acquire::AcquireCmd;
pub use cancel::CancelCmd;
pub use claim::ClaimCmd;
pub use forge::ForgeCmd;
pub use inspect::InspectCmd;
pub use listings::ListingsCmd;
pub use thaw_preview::ThawPreviewCmd;

use clap::Subcommand;

#[derive(Debug, Subcommand)]
pub enum Command {
    /// Create + fund + list a new vault in a single transaction.
    Forge(forge::ForgeArgs),

    /// Buy a listed vault by its pubkey.
    Acquire(acquire::AcquireArgs),

    /// Withdraw thawed tokens from a vault you own.
    Claim(claim::ClaimArgs),

    /// Close an active listing.
    Cancel(cancel::CancelArgs),

    /// Pretty-print a vault or listing account.
    Inspect(inspect::InspectArgs),

    /// Fetch every active listing on the program.
    Listings(listings::ListingsArgs),

    /// Preview how much would be withdrawable at a given timestamp.
    ThawPreview(thaw_preview::ThawPreviewArgs),
}
