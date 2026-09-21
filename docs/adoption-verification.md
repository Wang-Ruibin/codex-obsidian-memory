# Existing-vault adoption verification

[简体中文](zh-CN/adoption-verification.md)

## Scope and result

On 2026-09-21, the source-tree CLI and hook scripts were exercised on a temporary Markdown-only copy of an existing daily-use vault, on Windows with Python 3.14.6. This was an actual existing-vault adoption exercise, not a generated template fixture or a claim of third-party installation success. The original vault and global Codex configuration were not changed. Private note contents are not published here.

The copy contained 67 Markdown files, 28 project homes, 28 branch pages and 66 visible graph nodes. Validation reported no missing required notes, duplicate identities, broken links or orphan nodes. These counts describe this dated exercise, not all installations. The [captured result](evidence/adoption-2026-09-21.json) contains only counts and check outcomes.

| Check | Observed result |
|---|---|
| Adopt the existing custom layout without templates | Every original Markdown hash stayed unchanged |
| Inspect configuration and validate the graph | Memory enabled; validation passed |
| Load context for the real local GitHub project | The matching project home was included |
| Write a preference to the temporary copy | Missing disclosure was blocked |
| Retry with only a generic “Memory updated” entry | Still blocked; change evidence retained |
| Provide the note path and a concrete description | Stop accepted completion |
| Submit a new session identifier to the hook | The saved preference appeared in its context |
| Disable and enable the integration | Disabled hook was silent; enabling restored context |
| Uninstall the isolated integration | Copy and source notes were preserved |

Hook subprocess checks do not demonstrate model recall in an interactive conversation or confirm trust in a newly installed client. A user's report that they reached README step 3 identified a usability gap; it did not establish that their installation succeeded. That feedback led to explicit input locations, completion signals, scope checks and a save/new-conversation/read exercise in both READMEs.

## Reproduce safely

Run from a clone of this repository. Provide an existing vault and a local GitHub project already registered in it. The helper copies visible Markdown into a temporary directory, uses isolated configuration, and removes only that temporary test directory afterwards. It does not install a plugin into your everyday client, change global settings, or delete or move the source vault. Its output contains counts and pass/fail results, not note bodies. If a check fails, inspect your vault locally with `validate`; do not upload private notes as a bug report.

This example uses the custom layout exercised above. Replace both absolute paths and adjust every mapping to your own layout. On macOS/Linux replace `py -3` with `python3` and use local paths.

```text
py -3 scripts/verify_adoption.py --source-vault C:/path/to/existing-vault --project C:/path/to/github-project --path home=00-知识库首页.md --path global_memory=10-知识库/长期记忆.md --path maintenance=10-知识库/知识库维护.md --path template=10-知识库/模板.md --path project_index=20-项目/项目总览.md --path projects_dir=20-项目 --path weekly_brief=10-知识库/每周开工简报.md --path monthly_audit=10-知识库/每月知识体检.md
```

Success means exit code 0 and every value under `checks` is `true`. The script verifies source and copy hashes rather than relying on a successful process exit alone. See the [migration guide](../plugins/codex-obsidian-memory/skills/codex-obsidian-memory/references/migration.md) for normal setup.

## Lessons for adoption and troubleshooting

- Map an existing layout with `--no-template`; validation passing and repository eligibility are separate checks.
- Verify a saved fact through a new session, with its note identified. “I remembered it” alone is not evidence of persistence.
- If Stop requests another review, supply each changed note's vault-relative path and a specific description. Identical basenames in different project folders need their directory paths.
- Keep the exact branch spelling inside notes. Use distinct filenames on Windows for branch names that differ only by case.
- Record platform, input layout, expected behavior and observed results when reporting a failure. Share sanitized errors rather than the vault itself.

## Release decision

The runtime fixes are packaged as 0.4.1. Defer a first **stable GitHub Release**: this exercise supports existing-vault adoption and hook behavior, but does not cover a new user's marketplace installation, interactive hook trust, or independent user confirmation. Before labeling a release stable, record at least one fresh-client installation through trust and new-conversation recall, and resolve any failures. A versioned source update is not a claim that this wider acceptance gate has passed.
