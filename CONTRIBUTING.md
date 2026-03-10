# Contributing to geas

Thanks for the interest. geas is a small project but contributions of any size
are welcome — bug reports, docs fixes, reviews, and new features alike.

## Ground rules

- Every change lands through a pull request against `main`.
- One logical change per PR. Split a feature into a chain of PRs if it grows.
- Keep commits **conventional**: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`,
  `ci:`, `chore:`, `perf:`. A scope is nice: `feat(sdk): …`.
- `cargo fmt --all` + `npx prettier --write` before pushing.
- `cargo clippy --workspace -- -W warnings` should be clean (warnings OK, but
  treat them as someone's next PR).

## Development loop

```
git clone https://github.com/Geasfun/geas
cd geas
anchor build              # program
cd sdk && npm install
npm run build
npm test
```

Integration tests that hit devnet are guarded behind the `GEAS_DEVNET_TESTS=1`
env var so casual contributors don't burn airdrop SOL by accident.

## Filing issues

Please use the issue templates. Minimum useful report:

- What you expected to happen
- What actually happened
- A reproducer (Rust snippet / TS snippet / tx signature)
- Network (localnet / devnet / mainnet) and commit SHA

## Security

Do **not** file security issues as public GitHub issues. See `SECURITY.md`.

## Code of conduct

We follow the [Contributor Covenant 2.1](./CODE_OF_CONDUCT.md). Be kind.

## License

By contributing, you agree that your contributions will be licensed under the
MIT license that covers the project.
