# Contributing

[简体中文](docs/zh-CN/CONTRIBUTING.md)

Thanks for helping improve Codex Obsidian Memory. The whole workflow below can be done by talking to your agent — or by typing the commands yourself.

## Set up and test

```bash
git clone git@github.com:Wang-Ruibin/codex-obsidian-memory.git
cd codex-obsidian-memory
python -m unittest discover -s tests -v
```

The runtime uses Python 3.11+ and the standard library only, so there is nothing to install. Prefer conversation? Hand the repository to your agent:

```text
Set up the codex-obsidian-memory repository locally and run its test suite.
Tell me the results and anything that failed.
```

## Ground rules

- Keep vault operations additive unless a user explicitly approves replacing a reviewed template.
- Never read credentials, private keys, cookies or unrelated personal files.
- Preserve exact `github_repo` and `working_branch` routing.
- Add behavioral tests for routing, lifecycle, migration and uninstall fixes.
- Update the English source and matching `zh-CN` translation in the same change, keeping headings, code blocks, warnings and local links structurally aligned.

Open an issue before a large schema migration. Pull requests should explain the user-visible outcome, tests run and compatibility impact.
