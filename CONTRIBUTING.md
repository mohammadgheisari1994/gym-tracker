# Contributing

## Workflow

1. Open a GitHub Issue describing the feature or bug (English only).
2. Branch from `main`:
   - `feat/<issue-number>-<short-description>`
   - `fix/<issue-number>-<short-description>`
   - `chore/<issue-number>-<short-description>`
3. Make the change. Keep it focused on the one issue.
4. Run `ruff check .`, `ruff format --check .`, and `pytest` locally.
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/),
   referencing the issue number in the subject, e.g.
   `feat: add rest timer #7`.
6. Open a Pull Request with a test-plan checklist in the body.
7. Wait for CI to pass, merge, then delete the branch.

## Ground rules

Read [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md). The short version: small
changes, root-cause fixes, clean layering, tests with new logic, no secrets in
the repo, English everywhere in code and docs.
