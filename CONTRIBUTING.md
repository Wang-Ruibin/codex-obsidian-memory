# Contributing

Thanks for improving Codex Obsidian Memory.

## Development setup

The runtime uses Python 3.11+ and the standard library only.

```bash
git clone git@github.com:Wang-Ruibin/codex-obsidian-memory.git
cd codex-obsidian-memory
python -m unittest discover -s tests -v
```

## Change rules

- Keep vault operations additive unless a user explicitly asks to replace a reviewed template file.
- Never add code that reads credentials, private keys, cookies or unrelated personal files.
- Preserve exact `github_repo` and `working_branch` routing.
- Add a behavioral test for every routing, lifecycle, migration or uninstall fix.
- Update the bundled Skill and README when the CLI changes.

Open an issue before a large schema migration. Pull requests should explain the user-visible outcome, tests run and any compatibility impact.
