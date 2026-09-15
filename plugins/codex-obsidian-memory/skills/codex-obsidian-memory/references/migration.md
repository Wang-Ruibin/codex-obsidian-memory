# Adopting an existing vault

[简体中文](zh-CN/migration.md)

Already have an Obsidian vault? You do not need to rearrange it by hand. Tell Codex where it is and what you want to keep:

```text
Use $codex-obsidian-memory to adopt my existing vault at /absolute/path/to/vault. Keep my current folders and notes, do not overwrite anything, ask me before changing global Codex configuration, and validate the result.
```

Before continuing, back up the vault or place it under version control. Codex should inspect the layout, show you the proposed mapping, and wait for your confirmation before making changes.

## What Codex should preserve

- Existing notes remain untouched. If the vault already uses the default layout, setup adds only missing template files.
- A custom layout is mapped instead of replaced. All mapped paths stay inside the vault.
- Each GitHub repository keeps one project folder and one project home. Branch-specific progress stays on its matching branch page.
- Every project home remains linked from the project index, and its branch or supporting pages remain linked from that project home.
- Normal memory use starts only after validation reports no missing required notes, duplicate identities, broken Wiki links or orphan nodes.

## Manual path reference

Most users can stop here and let Codex build the mapping. If you need to review or enter the mapping yourself, these are the available path keys:

| Key | Purpose | Default |
|---|---|---|
| `home` | Memory home | `00-memory-home.md` |
| `global_memory` | Cross-project preferences | `10-memory/global-memory.md` |
| `maintenance` | Maintenance hub | `10-memory/maintenance.md` |
| `template` | Project and branch template | `10-memory/project-template.md` |
| `project_index` | Repository index | `20-projects/project-index.md` |
| `projects_dir` | Repository folders | `20-projects` |
| `weekly_brief` | Weekly report | `10-memory/weekly-brief.md` |
| `monthly_audit` | Monthly report | `10-memory/monthly-audit.md` |

## Manual example

From the Skill directory, the following command adopts a custom layout without copying default templates. Replace the vault and owner values first, then adjust the note paths to match your vault:

```text
python ../../scripts/memoryctl.py init --vault /absolute/path/to/vault --github-owner my-account --no-template --path home=Home.md --path global_memory=Knowledge/Global.md --path maintenance=Knowledge/Maintenance.md --path template=Knowledge/Project-template.md --path project_index=Projects/Index.md --path projects_dir=Projects --path weekly_brief=Knowledge/Weekly.md --path monthly_audit=Knowledge/Monthly.md
```

On Windows, use `py.exe` if `python` is unavailable. Run `status` and `validate` immediately afterwards. If either check reports a problem, keep automatic memory paused and ask Codex to explain what needs attention.
