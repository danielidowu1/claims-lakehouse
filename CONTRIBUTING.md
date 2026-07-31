# Contributing to Claims Lakehouse

Thanks for your interest — contributions of every size are welcome. 🎉

## Ways to contribute

- 🐛 **Report a bug** or 💡 **suggest a feature** by opening an issue.
- 🌱 **Pick a `good first issue`** — these are scoped for newcomers.
- 🔧 **Take a roadmap task** (bronze / silver / gold / CI / dashboard).
- 📖 **Improve docs** — clarity fixes are genuinely valuable.

## Workflow

1. **Fork** the repo and create a branch: `git checkout -b feat/short-description`
2. Make your change. Keep PRs focused — one logical change each.
3. **Run checks locally** before pushing:
   ```bash
   make lint
   make test
   ```
4. **Open a Pull Request** against `main`. Describe what and why.
5. A maintainer reviews. CI must pass before merge.

## Conventions

- **Python:** formatted/linted with `ruff`. Type hints encouraged.
- **Commits:** short, present tense (e.g. `add silver dedup step`).
- **Data:** never commit raw or processed data — it's gitignored for a reason.
- **Secrets:** never commit `.env`, AWS keys, or credentials.

## Good first issues

New here? Look for issues labeled `good first issue`. Some starter ideas:

- Add a data-quality check to the bronze load (row counts, null checks).
- Write a unit test for a silver transformation.
- Add a new dimension table to the gold layer.
- Document one of the DE-SynPUF claim files in `docs/`.

## Questions?

Open a [Discussion](../../discussions) or comment on an issue. Be patient and kind — we're all learning.
