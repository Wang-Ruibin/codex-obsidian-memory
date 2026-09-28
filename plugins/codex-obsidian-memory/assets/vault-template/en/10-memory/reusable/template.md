---
type: system-template
status: active
---

# Reusable lesson template

← [[10-memory/reusable/index|Reusable experience index]]

## When to create a lesson

Keep only verified methods with transferable value. Unverified ideas stay in project Open questions. Search for an existing lesson first. Keep project events in project notes and the general method here. Do not copy transcripts or secrets.

## Topic page

```markdown
---
type: reusable-memory
status: verified
summary: One sentence describing the problem and result
keywords: problem technology environment
source_repo: OWNER/REPOSITORY
source_branch: exact-branch
source_note: 20-projects/repository/branch-page.md
verified_on: YYYY-MM-DD
---

# Topic

← [[10-memory/reusable/index|Reusable experience index]]

## Applies when
Describe the problem, environment, versions and prerequisites.

## Method and reason
Explain what worked and why, without copying project-specific progress.

## Limitations and failures
Describe where this does not apply and known failed approaches.

## Evidence
State what was actually verified and where to find the supporting result.
```

Use scalar frontmatter values. `source_note` is an exact vault-relative path to the source project home or a directly linked child. Preserve the source's exact branch; leave `source_branch` empty for a repository-level note. Adapt links and paths to custom layouts. Source fields are plain provenance, not Wiki links, so the existing graph bridge remains unchanged.

## Maintenance

Add a summary and link to the index; link the index from memory home. Set `verified_on` only after verification, not after an editorial edit. Keep conflicting conditions explicit and recheck them before use. Mark obsolete lessons `status: retired`, retain the file and mark its index entry; do not silently overwrite contradictory evidence or automatically move or delete notes.
