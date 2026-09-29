# Automatic runtime preparation

[简体中文](zh-CN/runtime.md)

Users install the memory plugin, not Python dependencies. Prepare its runtime during the authorized setup workflow, before initialization and Hook trust. This is separate from vault registration and does not create or change notes.

## Entry points

From the Skill directory:

```bash
sh ../../scripts/memoryctl.sh prepare-runtime
sh ../../scripts/memoryctl.sh status
sh ../../scripts/memoryctl.sh local-register --path /absolute/path/to/project
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/memoryctl.ps1 -Action prepare-runtime
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/memoryctl.ps1 -Action status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/memoryctl.ps1 -Action local-register --path C:\projects\example
```

The launchers accept all memory CLI commands. `hook` handles the lifecycle JSON protocol, `routine` invokes the routine runner, and `python-path` prints the resolved interpreter for scheduler installation. Preserve stdin, arguments, stdout and exit codes when embedding these entry points.

## Selection and downloads

Preparation first checks its cached interpreter, then existing Python 3.11+ installations. Without one, it downloads a pinned uv bootstrap archive from the official `astral-sh/uv` GitHub release, checks the SHA-256 recorded in `assets/runtime/uv-assets.txt`, and uses uv to prepare private Python 3.12 from Astral's Python distributions. No pip packages are installed. The bootstrap tool and download/extraction staging directory are deleted in a finally/trap cleanup; only the selected runtime and interpreter-path marker remain.

The private directory defaults to `$CODEX_HOME/obsidian-memory/runtime/<OS>-<architecture>` or the usual user `.codex` directory. Windows, Linux and macOS use separate directories. `CODEX_OBSIDIAN_RUNTIME_DIR` can override it for an isolated test or deployment. No system Python is replaced, no global PATH or shell profile is edited, and no Windows Python registry entry or executable shim is installed. All bootstrap options disable uv project configuration and persistent download caches. No notes or credentials are uploaded.

Automatic downloads support Windows x64/ARM64, glibc Linux x64/ARM64 (including WSL), and macOS Intel/Apple Silicon. Other platforms can use an existing compatible interpreter; do not claim automatic managed-runtime support without verification. First-time private preparation needs HTTPS access to GitHub/Astral distribution assets. Offline setups work with an existing compatible runtime; if none exists, report the download blocker instead of telling the user to manually configure dependencies.

## Daily operation and cleanup

Hooks and normal CLI commands only use a cached or existing compatible interpreter. They never start downloads. If it is unavailable, the agent should run preparation explicitly and explain any network or permission failure. Repeating preparation reuses a valid runtime. `prepare-runtime --managed` intentionally selects a private runtime even when system Python exists; it is useful for controlled installation tests and does not force a redownload when the private cache is valid.

A short-lived `prepare.lock` directory prevents concurrent setup. Inspect an interrupted preparation before removing a stale lock. The configured runtime can remain in use by hooks and scheduled tasks: do not delete it as a temporary test artifact. Temporary test environments must use a separate runtime directory and be cleaned after verification. Uninstall retains runtime files alongside other integration residue; remove that exact private runtime only when the integration and any referencing tasks are no longer using it, never the vault or system Python.

## Development and verification

Development still uses Python 3.11+ and the standard library. Test setup on Windows and POSIX, reuse of existing Python, cached operation without Python on PATH, lifecycle stdin, Unicode/spaced arguments, exit-code propagation, checksum failure and temporary-file cleanup. Perform a separate live private-download check on supported release platforms. Changing launcher commands in `hooks.json` requires normal host review/trust; do not persistently bypass that review.

Sources: [uv Python management](https://docs.astral.sh/uv/guides/install-python/), [uv command reference](https://docs.astral.sh/uv/reference/cli/).
