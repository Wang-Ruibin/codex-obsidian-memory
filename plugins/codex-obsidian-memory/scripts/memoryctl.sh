#!/bin/sh
# Existing Python first; network access only during explicit prepare-runtime.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
platform=$(uname -s)
architecture=$(uname -m)
runtime_root=${CODEX_OBSIDIAN_RUNTIME_DIR:-${CODEX_HOME:-${HOME}/.codex}/obsidian-memory/runtime/${platform}-${architecture}}
cache_file=${runtime_root}/python-path.txt
action=${1:-help}
if [ "$#" -gt 0 ]; then shift; fi
probe='import sys; sys.exit(1) if sys.version_info < (3,11) else None; print(sys.executable)'

detect_python() {
    if [ -f "$cache_file" ]; then
        IFS= read -r cached < "$cache_file" || true
        if [ -n "${cached:-}" ] && [ -x "$cached" ]; then
            if [ "${managed:-false}" = false ] || [ "${cached#"$runtime_root"/python/}" != "$cached" ]; then
                if selected=$("$cached" -I -c "$probe" 2>/dev/null); then return 0; fi
            fi
        fi
    fi
    if [ "${managed:-false}" = false ]; then
        for candidate in python3 python; do
            if command -v "$candidate" >/dev/null 2>&1; then
                if selected=$("$candidate" -I -c "$probe" 2>/dev/null); then return 0; fi
            fi
        done
    fi
    return 1
}

prepare_runtime() {
    managed=false
    if [ "${1:-}" = --managed ]; then managed=true; shift; fi
    [ "$#" -eq 0 ] || { printf 'Usage: memoryctl.sh prepare-runtime [--managed]\n' >&2; exit 2; }
    mkdir -p "$runtime_root"
    if ! mkdir "$runtime_root/prepare.lock" 2>/dev/null; then
        printf 'Runtime preparation is already running. Retry after it finishes.\n' >&2
        exit 1
    fi
    staging=''
    cleanup() {
        if [ -n "$staging" ] && [ -d "$staging" ]; then rm -rf -- "$staging"; fi
        rmdir "$runtime_root/prepare.lock" 2>/dev/null || true
    }
    trap cleanup EXIT
    trap 'exit 130' INT TERM HUP
    if ! detect_python; then
        case "$architecture" in x86_64|amd64) cpu=x86_64 ;; aarch64|arm64) cpu=aarch64 ;; *) printf 'Unsupported CPU for automatic runtime setup.\n' >&2; exit 1 ;; esac
        case "$platform" in Linux) target=${cpu}-unknown-linux-gnu ;; Darwin) target=${cpu}-apple-darwin ;; *) printf 'Unsupported OS for automatic runtime setup.\n' >&2; exit 1 ;; esac
        manifest="$script_dir/../assets/runtime/uv-assets.txt"
        version=$(awk '$1=="version" {print $2}' "$manifest")
        archive="uv-$target.tar.gz"
        expected=$(awk -v asset="$archive" '$1==asset {print $2}' "$manifest")
        [ "${#expected}" -eq 64 ] || { printf 'Missing pinned runtime checksum.\n' >&2; exit 1; }
        staging=$(mktemp -d "$runtime_root/.prepare.XXXXXX")
        url="https://github.com/astral-sh/uv/releases/download/$version/$archive"
        printf 'Preparing a private Python runtime for this plugin...\n' >&2
        if command -v curl >/dev/null 2>&1; then
            curl --fail --location --silent --show-error --proto '=https' --tlsv1.2 "$url" -o "$staging/$archive"
        elif command -v wget >/dev/null 2>&1; then
            wget --https-only -q "$url" -O "$staging/$archive"
        else
            printf 'No HTTPS downloader is available. Ask Codex to prepare the runtime on this machine.\n' >&2; exit 1
        fi
        if command -v sha256sum >/dev/null 2>&1; then
            actual=$(sha256sum "$staging/$archive" | awk '{print $1}')
        else
            actual=$(shasum -a 256 "$staging/$archive" | awk '{print $1}')
        fi
        [ "$actual" = "$expected" ] || { printf 'Runtime bootstrap checksum mismatch.\n' >&2; exit 1; }
        tar -xzf "$staging/$archive" -C "$staging"
        uv="$staging/uv-$target/uv"
        export UV_PYTHON_INSTALL_DIR="$runtime_root/python"
        export UV_NO_MODIFY_PATH=1
        "$uv" python install 3.12 --no-bin --no-registry --no-config --no-cache
        selected=$("$uv" python find 3.12 --managed-python --no-python-downloads --no-config --no-cache)
        selected=$("$selected" -I -c "$probe")
    fi
    printf '%s\n' "$selected" > "$runtime_root/python-path.tmp"
    mv -f "$runtime_root/python-path.tmp" "$cache_file"
    printf '%s\n' "$selected"
}

case "$action" in
    prepare-runtime) prepare_runtime "$@"; exit 0 ;;
    help|--help|-h) printf 'Usage: sh memoryctl.sh prepare-runtime [--managed] | python-path | hook | routine ARGS | COMMAND ARGS\n'; exit 0 ;;
esac
if ! detect_python; then
    printf 'Plugin runtime is not ready. Ask Codex to run: sh "%s/memoryctl.sh" prepare-runtime\n' "$script_dir" >&2
    exit 1
fi
case "$action" in
    python-path) printf '%s\n' "$selected" ;;
    hook) exec "$selected" -B "$script_dir/hook.py" "$@" ;;
    routine) exec "$selected" -B "$script_dir/routine_runner.py" "$@" ;;
    *) exec "$selected" -B "$script_dir/memoryctl.py" "$action" "$@" ;;
esac
