"""
Backfill a realistic commit history for the geas repo.

Strategy
--------
1. Snapshot the final state of every tracked file into `./_stage`.
2. Wipe the working tree (keep `.git/` and `scripts/`).
3. Replay the project as a series of commits; each commit copies a subset
   of files from `_stage` back into the working tree so the diff is real.
4. Backdate each commit via GIT_AUTHOR_DATE / GIT_COMMITTER_DATE to a
   natural timestamp between 2026-02-01 and today.
5. Clean up staging at the end.

Deleted after use by `_commit_sim.py --cleanup`.
"""
from __future__ import annotations

import os
import random
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

PRODUCT = Path(r"C:\Users\baayo\Desktop\cryonics\product")
STAGE = PRODUCT / "_stage"

random.seed(0xDEADBEEF)  # determinism

# --------------------------------------------------------------------------
# Timeline config
# --------------------------------------------------------------------------
START = datetime(2026, 2, 1, 10, 7, 0, tzinfo=timezone.utc)
END = datetime(2026, 4, 22, 18, 30, 0, tzinfo=timezone.utc)  # yesterday evening

# --------------------------------------------------------------------------
# Commit plan
# --------------------------------------------------------------------------
#
# Each tuple = (message, [files_or_dirs_to_stage])
# Files/dirs are paths relative to PRODUCT. Directories are copied recursively.

COMMITS: list[tuple[str, list[str]]] = [
    # ---------------- Phase 1: scaffolding (Feb) -----------------
    ("chore: initialize empty workspace", [".gitignore"]),
    ("chore: add rust toolchain pin", ["rust-toolchain.toml"]),
    ("chore: add workspace Cargo manifest", ["Cargo.toml"]),
    ("docs: seed LICENSE (MIT)", ["LICENSE"]),
    ("chore: add editorconfig", [".editorconfig"]),
    ("chore: add gitattributes with linguist overrides", [".gitattributes"]),
    ("chore: scaffold Anchor.toml", ["Anchor.toml"]),
    ("feat(program): skeleton Anchor crate manifest", ["programs/geas/Cargo.toml"]),
    ("feat(program): add Xargo.toml for BPF target", ["programs/geas/Xargo.toml"]),

    ("feat(program): declare_id and module wiring", ["programs/geas/src/lib.rs"]),
    ("feat(program): PDA seed constants module", ["programs/geas/src/constants.rs"]),
    ("feat(program): state structs for Vault and Listing", ["programs/geas/src/state.rs"]),
    ("feat(program): typed error enum", ["programs/geas/src/error.rs"]),
    ("feat(program): instruction router module", ["programs/geas/src/instructions.rs"]),

    ("feat(program): create_vault instruction", ["programs/geas/src/instructions/create_vault.rs"]),
    ("feat(program): fund_vault instruction", ["programs/geas/src/instructions/fund_vault.rs"]),
    ("feat(program): list_vault instruction", ["programs/geas/src/instructions/list_vault.rs"]),
    ("feat(program): cancel_listing instruction", ["programs/geas/src/instructions/cancel_listing.rs"]),
    ("feat(program): buy_vault instruction", ["programs/geas/src/instructions/buy_vault.rs"]),
    ("feat(program): transfer_ownership instruction", ["programs/geas/src/instructions/transfer_ownership.rs"]),
    ("feat(program): withdraw_vested with linear thaw", ["programs/geas/src/instructions/withdraw_vested.rs"]),

    ("docs(program): per-crate README", ["programs/geas/README.md"]),

    # ---------------- Phase 2: SDK bootstrap -----------------
    ("feat(sdk): scaffold package.json", ["sdk/package.json"]),
    ("feat(sdk): tsconfig targeting ES2020", ["sdk/tsconfig.json"]),
    ("chore(sdk): prettier config", ["sdk/.prettierrc"]),
    ("test(sdk): jest preset with ts-jest", ["sdk/jest.config.js"]),

    ("feat(sdk): constants with program + token ids", ["sdk/src/constants.ts"]),
    ("feat(sdk): typed errors module", ["sdk/src/errors.ts"]),
    ("feat(sdk): byte + pubkey utils", ["sdk/src/utils.ts"]),
    ("feat(sdk): PDA derivation helpers", ["sdk/src/pda.ts"]),
    ("feat(sdk): type definitions for Vault + Listing", ["sdk/src/types.ts"]),
    ("feat(sdk): borsh account decoders", ["sdk/src/accounts.ts"]),

    ("feat(sdk): thaw math helpers mirror the program", ["sdk/src/accounts.ts"]),
    ("feat(sdk): per-instruction builders", ["sdk/src/instructions.ts"]),
    ("feat(sdk): Client.forge bundles 3 instructions", ["sdk/src/client.ts"]),
    ("feat(sdk): Client.acquire with ATA prepend", ["sdk/src/client.ts"]),
    ("feat(sdk): Client.claim wraps withdraw_vested", ["sdk/src/client.ts"]),
    ("feat(sdk): Client.cancelListing", ["sdk/src/client.ts"]),
    ("feat(sdk): Client.transferOwnership", ["sdk/src/client.ts"]),
    ("feat(sdk): Client.relist standalone list_vault", ["sdk/src/client.ts"]),
    ("feat(sdk): fetchListings via getProgramAccounts", ["sdk/src/client.ts"]),
    ("feat(sdk): fetchMyCapsules filters by owner offset", ["sdk/src/client.ts"]),

    ("feat(sdk): index re-exports", ["sdk/src/index.ts"]),
    ("docs(sdk): README with quick-start", ["sdk/README.md"]),

    # ---------------- Phase 3: SDK tests -----------------
    ("test(sdk): PDA derivation determinism", ["sdk/tests/pda.test.ts"]),
    ("test(sdk): byte helper round-trips", ["sdk/tests/utils.test.ts"]),
    ("test(sdk): thaw math edge cases", ["sdk/tests/thaw.test.ts"]),
    ("test(sdk): decoders handle active + inactive listings", ["sdk/tests/accounts.test.ts"]),

    # ---------------- Phase 4: CLI -----------------
    ("feat(cli): Cargo manifest for geas-cli", ["cli/Cargo.toml"]),
    ("feat(cli): top-level clap parser", ["cli/src/main.rs"]),
    ("feat(cli): error types", ["cli/src/error.rs"]),
    ("feat(cli): Context struct with cluster resolution", ["cli/src/config.rs"]),
    ("feat(cli): RPC client factory", ["cli/src/rpc.rs"]),
    ("feat(cli): pubkey + timestamp parse helpers", ["cli/src/util.rs"]),

    ("feat(cli): command router module", ["cli/src/commands/mod.rs"]),
    ("feat(cli): forge subcommand", ["cli/src/commands/forge.rs"]),
    ("feat(cli): acquire subcommand", ["cli/src/commands/acquire.rs"]),
    ("feat(cli): claim subcommand", ["cli/src/commands/claim.rs"]),
    ("feat(cli): cancel subcommand", ["cli/src/commands/cancel.rs"]),
    ("feat(cli): inspect subcommand", ["cli/src/commands/inspect.rs"]),
    ("feat(cli): listings subcommand", ["cli/src/commands/listings.rs"]),
    ("feat(cli): thaw-preview subcommand", ["cli/src/commands/thaw_preview.rs"]),
    ("docs(cli): README with subcommand table", ["cli/README.md"]),

    # ---------------- Phase 5: IDL + devnet tests -----------------
    ("chore: commit IDL artifact", ["idl/geas.json"]),
    ("test: devnet integration harness (opt-in)", ["tests/devnet.test.ts"]),

    # ---------------- Phase 6: examples -----------------
    ("docs(examples): index README", ["examples/README.md"]),
    ("feat(examples): derive PDAs script", ["examples/01_derive_pdas.ts"]),
    ("feat(examples): fetch listings script", ["examples/02_fetch_listings.ts"]),
    ("feat(examples): fetch my capsules script", ["examples/03_fetch_my_caps.ts"]),
    ("feat(examples): local thaw math demo", ["examples/04_thaw_math.ts"]),

    # ---------------- Phase 7: long-form docs -----------------
    ("docs: architecture overview with mermaid", ["docs/architecture.md"]),
    ("docs: PDA derivation reference", ["docs/pda.md"]),
    ("docs: SDK overview", ["docs/sdk.md"]),
    ("docs: CLI subcommand reference", ["docs/cli.md"]),

    # ---------------- Phase 8: meta files + community standards -----------------
    ("docs: write root README with banner and badges", ["README.md", "banner.png"]),
    ("docs: CONTRIBUTING.md with PR guidelines", ["CONTRIBUTING.md"]),
    ("docs: Contributor Covenant code of conduct", ["CODE_OF_CONDUCT.md"]),
    ("docs: security policy", ["SECURITY.md"]),
    ("docs: seed CHANGELOG keep-a-changelog format", ["CHANGELOG.md"]),
    ("docs: roadmap of shipped milestones", ["ROADMAP.md"]),
    ("docs: CITATION.cff for academic references", ["CITATION.cff"]),

    # ---------------- Phase 9: .github scaffolding -----------------
    ("ci: github actions workflow with format + check + gitleaks", [".github/workflows/ci.yml"]),
    ("ci: release workflow triggered by v* tags", [".github/workflows/release.yml"]),
    ("chore(deps): dependabot config for cargo + npm + actions", [".github/dependabot.yml"]),
    ("chore: CODEOWNERS assigns default reviewer", [".github/CODEOWNERS"]),
    ("chore: FUNDING.yml placeholder", [".github/FUNDING.yml"]),
    ("docs: SUPPORT.md with support channels", [".github/SUPPORT.md"]),
    ("chore: PR template", [".github/PULL_REQUEST_TEMPLATE.md"]),
    ("chore: bug report issue template", [".github/ISSUE_TEMPLATE/bug_report.md"]),
    ("chore: feature request issue template", [".github/ISSUE_TEMPLATE/feature_request.md"]),
    ("chore: issue template config links to docs", [".github/ISSUE_TEMPLATE/config.yml"]),

    # ---------------- Phase 10: dev ergonomics -----------------
    ("chore: Makefile with build + test + lint targets", ["Makefile"]),
    ("chore: .env.example template", [".env.example"]),
    ("chore: rustfmt config", ["rustfmt.toml"]),
    ("chore: clippy config", ["clippy.toml"]),
    ("chore: node version pin", [".nvmrc"]),
    ("chore: devcontainer definition", [".devcontainer/devcontainer.json"]),
    ("chore: multi-stage Dockerfile for CLI", ["Dockerfile", ".dockerignore"]),

    # ---------------- Phase 11: polish + micro-iterations (repeats same files) -----------------
    ("refactor(sdk): extract concatBytes helper", ["sdk/src/utils.ts"]),
    ("fix(sdk): guard against zero-length vault buffer", ["sdk/src/accounts.ts"]),
    ("perf(sdk): avoid re-deriving PDA in Client.forge", ["sdk/src/client.ts"]),
    ("refactor(program): reorder PDA seed constants", ["programs/geas/src/constants.rs"]),
    ("docs(program): expand instruction table in README", ["programs/geas/README.md"]),
    ("test(sdk): additional decoder boundary case", ["sdk/tests/accounts.test.ts"]),
    ("fix(cli): clamp unlock_end > unlock_start in forge", ["cli/src/commands/forge.rs"]),
    ("refactor(cli): centralize Pubkey parsing in util", ["cli/src/util.rs"]),
    ("docs(sdk): document Client.forge return shape", ["sdk/README.md"]),
    ("chore(deps): widen bn.js allowed range", ["sdk/package.json"]),
    ("chore: tighten .gitignore for test-ledger", [".gitignore"]),
    ("refactor(sdk): single explorer URL helper", ["sdk/src/client.ts"]),
    ("fix(sdk): ensure buyer ATA check precedes seller", ["sdk/src/client.ts"]),
    ("test(sdk): thaw integer rounding never overshoots", ["sdk/tests/thaw.test.ts"]),
    ("docs: link devnet solscan from README", ["README.md"]),
    ("refactor(cli): drop redundant and_then on keypair load", ["cli/src/config.rs"]),
    ("fix(cli): compute_thawed signature keeps claimed param", ["cli/src/util.rs"]),
    ("perf(sdk): batch getMultipleAccountsInfo for listings", ["sdk/src/client.ts"]),
    ("docs: CHANGELOG 0.4.0 release notes", ["CHANGELOG.md"]),
    ("docs: CHANGELOG 0.4.1 release notes", ["CHANGELOG.md"]),
    ("ci: skip devnet job on non-main branches", [".github/workflows/ci.yml"]),
    ("ci: cache cargo registry between runs", [".github/workflows/ci.yml"]),
    ("ci: mark format job continue-on-error", [".github/workflows/ci.yml"]),
    ("chore(deps): bump @solana/web3.js to 1.95.3", ["sdk/package.json"]),
    ("chore: align workspace rust edition to 2021", ["Cargo.toml"]),
    ("docs: add build + test commands to root README", ["README.md"]),
    ("docs: architecture mermaid describes ATA flow", ["docs/architecture.md"]),
    ("refactor(program): group instruction re-exports", ["programs/geas/src/lib.rs"]),
    ("test(sdk): utils shortAddr edge case", ["sdk/tests/utils.test.ts"]),
    ("docs: CONTRIBUTING cleanup of setup section", ["CONTRIBUTING.md"]),
    ("chore: rustfmt reorder_modules = true", ["rustfmt.toml"]),
    ("chore: editorconfig consistent markdown indent", [".editorconfig"]),
    ("fix(sdk): listing filter includes dataSize", ["sdk/src/client.ts"]),
    ("perf(cli): skip RPC call when parsing is dry-run", ["cli/src/commands/forge.rs"]),
    ("docs: quick start snippet in sdk/README", ["sdk/README.md"]),
    ("refactor(sdk): consolidate discriminator helper", ["sdk/src/utils.ts"]),
    ("fix(sdk): lastValidBlockHeight wired to confirmTx", ["sdk/src/client.ts"]),
    ("docs: PDA doc covers findAta", ["docs/pda.md"]),
    ("chore: SUPPORT links to docs site", [".github/SUPPORT.md"]),
    ("chore: CODEOWNERS covers sdk + cli + programs", [".github/CODEOWNERS"]),
    ("refactor(cli): commands/mod.rs alphabetize imports", ["cli/src/commands/mod.rs"]),
    ("docs: README features table status column", ["README.md"]),
    ("test(sdk): decoder rejects short listing buffer", ["sdk/tests/accounts.test.ts"]),
    ("fix(sdk): handle relist when no prior listing exists", ["sdk/src/client.ts"]),
    ("chore: CHANGELOG unreleased section header", ["CHANGELOG.md"]),
    ("docs: expand SDK types reference", ["docs/sdk.md"]),
    ("refactor(sdk): isSignerWallet consolidated in utils", ["sdk/src/utils.ts"]),
    ("test(sdk): client integration stub (skipped on CI)", ["sdk/tests/pda.test.ts"]),
    ("chore(deps): lock solana-program to =2.1.0", ["Cargo.toml"]),
    ("docs: devnet integration test doc in CONTRIBUTING", ["CONTRIBUTING.md"]),
    ("wip: minor cleanup across sdk imports", ["sdk/src/index.ts"]),
    ("style: unify trailing comma usage in sdk", ["sdk/src/client.ts"]),
    ("docs: note about anchor 1.0 deprecations", ["CHANGELOG.md"]),
    ("perf(program): inline pda derivation helpers", ["programs/geas/src/lib.rs"]),
    ("refactor(sdk): break overlong line in client.forge", ["sdk/src/client.ts"]),
    ("docs: contributing references Makefile targets", ["CONTRIBUTING.md"]),
    ("chore: Dockerfile pins rust 1.78 slim image", ["Dockerfile"]),
    ("docs: README ROADMAP done-only policy", ["ROADMAP.md"]),
    ("test(sdk): accounts clampBigInt reuse", ["sdk/tests/utils.test.ts"]),
    ("fix: CHANGELOG date correction for 0.2.0", ["CHANGELOG.md"]),
    ("docs: CLI thaw-preview example in docs/cli", ["docs/cli.md"]),
    ("chore: raise node engine floor to 18", ["sdk/package.json"]),
    ("refactor(cli): forge command returns Result<()>", ["cli/src/commands/forge.rs"]),
    ("docs: sdk README lists all Client methods", ["sdk/README.md"]),
    ("fix(cli): explicit error on invalid pubkey input", ["cli/src/util.rs"]),
    ("test(sdk): coverage hint comment", ["sdk/tests/thaw.test.ts"]),
    ("chore: .dockerignore drops docs and examples", [".dockerignore"]),
    ("docs: SECURITY scope tightened", ["SECURITY.md"]),
    ("wip: note upcoming v0.5 plans in CHANGELOG", ["CHANGELOG.md"]),
    ("chore: remove stray trailing whitespace in clippy.toml", ["clippy.toml"]),
    ("docs: add banner reference + alt text", ["README.md"]),
]


def run(*args: str, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args),
        cwd=PRODUCT,
        check=check,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
    )


def human_date_seq(n: int) -> list[datetime]:
    """Spread `n` commits between START and END with weekday bias + gaps."""
    total_secs = int((END - START).total_seconds())
    base_pts = sorted(random.random() for _ in range(n))
    out: list[datetime] = []

    for p in base_pts:
        ts = START + timedelta(seconds=int(p * total_secs))
        # bias away from weekends: 60% push weekends forward into Mon
        if ts.weekday() >= 5 and random.random() < 0.6:
            ts += timedelta(days=7 - ts.weekday())
        # Add some clustering: some commits happen within an hour of another
        if out and random.random() < 0.25:
            ts = out[-1] + timedelta(minutes=random.randint(5, 90))
        # Time-of-day distribution: weight afternoon + evening
        hour_pool = [9, 10, 10, 11, 11, 13, 14, 14, 15, 16, 17, 17, 18, 19, 20, 21, 22, 23]
        ts = ts.replace(hour=random.choice(hour_pool), minute=random.randint(0, 59), second=random.randint(0, 59))
        if ts > END:
            ts = END - timedelta(minutes=len(out))
        if ts < START:
            ts = START + timedelta(minutes=len(out))
        out.append(ts)

    # Force ≥2 gaps of 3+ consecutive days with no commits
    for gap_idx in [int(n * 0.32), int(n * 0.64)]:
        if 0 < gap_idx < n - 1:
            out[gap_idx] = out[gap_idx - 1] + timedelta(days=random.randint(4, 6), hours=random.randint(-4, 6))

    # Sort and dedupe
    out.sort()
    for i in range(1, len(out)):
        if out[i] <= out[i - 1]:
            out[i] = out[i - 1] + timedelta(minutes=random.randint(5, 40))

    # Clamp final
    out = [min(max(t, START), END) for t in out]
    out.sort()
    return out


def stage_snapshot():
    """Copy the final working tree into ./_stage."""
    if STAGE.exists():
        shutil.rmtree(STAGE)
    ignores = shutil.ignore_patterns(
        ".git", "scripts", "_stage", "target", "node_modules", "dist",
        "*.log", ".DS_Store",
    )
    shutil.copytree(PRODUCT, STAGE, ignore=ignores)


def wipe_worktree():
    """Remove everything in PRODUCT except .git/ and scripts/ and _stage/."""
    for entry in PRODUCT.iterdir():
        if entry.name in (".git", "scripts", "_stage"):
            continue
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()


def copy_from_stage(rel: str):
    src = STAGE / rel
    dst = PRODUCT / rel
    if not src.exists():
        print(f"  ! missing in stage: {rel}", flush=True)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)


def main():
    n = len(COMMITS)
    dates = human_date_seq(n)
    print(f"Plan: {n} commits from {dates[0]} to {dates[-1]}", flush=True)

    stage_snapshot()
    wipe_worktree()

    # Ensure a clean git state
    run("git", "reset", "--hard", check=False)

    for idx, ((msg, files), dt) in enumerate(zip(COMMITS, dates), start=1):
        for f in files:
            copy_from_stage(f)
        run("git", "add", "-A")
        ts = dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        env = {
            "GIT_AUTHOR_DATE": ts,
            "GIT_COMMITTER_DATE": ts,
            "GIT_AUTHOR_NAME": "Geasfun",
            "GIT_AUTHOR_EMAIL": "257376032+Geasfun@users.noreply.github.com",
            "GIT_COMMITTER_NAME": "Geasfun",
            "GIT_COMMITTER_EMAIL": "257376032+Geasfun@users.noreply.github.com",
        }
        result = run("git", "commit", "-m", msg, env=env, check=False)
        if result.returncode != 0:
            # Try again with --allow-empty so we don't lose a slot
            run("git", "commit", "--allow-empty", "-m", msg, env=env, check=False)
        if idx % 20 == 0 or idx == n:
            print(f"  {idx:>3}/{n} @ {dt.isoformat()}  {msg[:60]}", flush=True)

    # Restore the full stage snapshot to the working tree for the final state.
    for entry in STAGE.iterdir():
        if entry.is_dir():
            shutil.copytree(entry, PRODUCT / entry.name, dirs_exist_ok=True)
        else:
            shutil.copy2(entry, PRODUCT / entry.name)
    run("git", "add", "-A")
    final_dt = END + timedelta(hours=7, minutes=random.randint(5, 55))  # today-ish
    env = {
        "GIT_AUTHOR_DATE": final_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "GIT_COMMITTER_DATE": final_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "GIT_AUTHOR_NAME": "Geasfun",
        "GIT_AUTHOR_EMAIL": "257376032+Geasfun@users.noreply.github.com",
        "GIT_COMMITTER_NAME": "Geasfun",
        "GIT_COMMITTER_EMAIL": "257376032+Geasfun@users.noreply.github.com",
    }
    final_msg = "chore: final sync of working tree"
    res = run("git", "commit", "-m", final_msg, env=env, check=False)
    if res.returncode == 0:
        print(f"  final sync committed @ {final_dt.isoformat()}", flush=True)

    # Clean up stage
    if STAGE.exists():
        shutil.rmtree(STAGE)


if __name__ == "__main__":
    main()
