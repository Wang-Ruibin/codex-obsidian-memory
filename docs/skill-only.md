# Use memory without Hooks

[简体中文](zh-CN/skill-only.md) · [README](../README.md)

The standalone `codex-obsidian-memory-skill` is an alternative to the Hook plugin. It contains its own instructions, local scripts and templates. Copying its complete folder is enough; it does not need an installed plugin or a checkout of this repository.

## Install and set up

Send this to Codex:

```text
Use $skill-installer to install skills/codex-obsidian-memory-skill from
Wang-Ruibin/codex-obsidian-memory. Install only this Skill, keeping any existing
Hook integration unchanged. Verify that the complete Skill folder is available.
```

If it does not appear in the Skill picker, restart Codex. You can also copy the complete [Skill folder](../skills/codex-obsidian-memory-skill) into a personal or repository Skill location supported by your host. Keep all of its scripts, templates and references together. See the [official Skill documentation](https://learn.chatgpt.com/docs/build-skills) for host discovery and `$skill-installer` support.

Then ask:

```text
Use $codex-obsidian-memory-skill to set up my memory. Check its status first and
prepare its private runtime if necessary. Help me choose a vault location and
whether to use GitHub projects or only explicitly registered local projects.
Use English notes. Preserve any existing vault and show me the setup changes.
```

Codex reuses a compatible Python 3.11+ or prepares a private runtime. It does not change PATH, Codex settings, global guidance, Hooks, trust records or OS tasks. Network access is needed only if setup must download a runtime. The standalone configuration lives separately under `~/.codex/obsidian-memory-skill` (or your `CODEX_HOME`), and setup does not overwrite existing notes. You are ready when the Skill reports the intended vault and a healthy structure.

## Work in a project

Use a prompt such as:

```text
Use $codex-obsidian-memory-skill while continuing this project. Load the relevant
memory, check reusable experience, complete the work, and review any memory changes
before replying.
```

For a local folder without GitHub, explicitly ask the Skill to register that project first. Registration applies immediately, preserving a stable local project ID. GitHub projects use exact repository identity and configured scope; excluded repositories stay excluded. Branch progress belongs only to the current branch page.

The Skill starts a memory task, loads the current context, searches relevant prior work and finishes with a checked writeback review. If work is interrupted or context is compacted, ask it to resume the unfinished memory task with the same task ID. The original review baseline remains in place. You do not need to manage the underlying hashes or commands yourself.

When notes change, the final reply lists each changed file and what facts or sections changed, in your language. Check those facts and ask for corrections if needed. The review command checks file coverage and minimum explanations; it does not prove facts are true.

## Remember one ordinary chat

Ordinary chat memory is off by default. Say “Use $codex-obsidian-memory-skill to remember this conversation” to enable only the current chat. Say “Stop remembering this conversation” to stop content loading and saving while retaining its note. Existing GitHub and registered local-project memory keep their own route.

The note's filename follows the displayed chat title when the Skill next runs or you ask it to synchronize the title. A renamed chat does not lose its stored facts. Turning content memory off still allows those explicit title updates; ask to freeze title synchronization too if desired. No background process runs while the Skill is idle.

## Choose or switch editions

The Hook plugin automatically loads context and checks task-end disclosure. The standalone Skill performs these operations only when it is invoked; it cannot force invocation after every prompt or compaction, and it cannot block a host reply when skipped. Both share the same routing, retrieval and validation implementation, but the Skill has no continuous title watcher, scheduled-routine installer or directory-migration command. Explicitly mentioning the Skill gives you direct control over when it runs.

Installing the Skill does not disable or replace an existing Hook integration. Pick one writer for a task. If you want to switch, ask Codex to inspect both configurations, explain the switch and obtain any needed authorization before changing the existing installation. Reuse an existing vault with explicit path mappings and no template overwrite; attach existing local project IDs rather than creating duplicate homes. Each edition keeps its own environment-specific configuration and chat consent state.

To pause this edition, ask it to disable its own memory configuration. To remove it, use your host's normal Skill management; vault notes remain. Cleanup of retained local task state is a separate reviewed operation. Detailed commands and note fields are in the [Skill reference](../skills/codex-obsidian-memory-skill/references/usage.md).
