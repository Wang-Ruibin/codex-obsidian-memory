# Contributing

[简体中文](docs/zh-CN/CONTRIBUTING.md)

Thanks for improving Codex Obsidian Memory.

## Development setup

The runtime uses Python 3.11+ and the standard library only.

```bash
git clone git@github.com:Wang-Ruibin/codex-obsidian-memory.git
cd codex-obsidian-memory
python -m unittest discover -s tests -v
```

## Change rules

- Keep vault operations additive unless a user explicitly approves replacing a reviewed template.
- Never read credentials, private keys, cookies or unrelated personal files.
- Preserve exact `github_repo` and `working_branch` routing.
- Add behavioral tests for routing, lifecycle, migration and uninstall fixes.
- Update the English source and matching `zh-CN` translation in the same change.
- Keep headings, code blocks, warnings and local links structurally aligned across locales.

Open an issue before a large schema migration. Pull requests should explain the user-visible outcome, tests run and compatibility impact.
