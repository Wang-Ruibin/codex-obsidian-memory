#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
plugin_root="$(cd -- "${script_dir}/.." && pwd)"
data_home="${XDG_DATA_HOME:-${HOME}/.local/share}"
config_home="${XDG_CONFIG_HOME:-${HOME}/.config}"
automation_root="${data_home}/codex-obsidian-memory/automation"
unit_dir="${config_home}/systemd/user"
weekly_service="codex-obsidian-memory-weekly.service"
weekly_timer="codex-obsidian-memory-weekly.timer"
monthly_service="codex-obsidian-memory-monthly.service"
monthly_timer="codex-obsidian-memory-monthly.timer"

case "${automation_root}" in
    "${data_home}"/*) ;;
    *) printf 'Unsafe automation path: %s\n' "${automation_root}" >&2; exit 1 ;;
esac

if [[ "${1:-}" == "--uninstall" ]]; then
    systemctl --user disable --now "${weekly_timer}" "${monthly_timer}" >/dev/null 2>&1 || true
    rm -f -- \
        "${unit_dir}/${weekly_service}" \
        "${unit_dir}/${weekly_timer}" \
        "${unit_dir}/${monthly_service}" \
        "${unit_dir}/${monthly_timer}"
    systemctl --user daemon-reload
    if [[ -d "${automation_root}" ]]; then
        rm -rf -- "${automation_root}"
    fi
    printf 'automation_installed=false\n'
    exit 0
fi

if [[ $# -ne 0 ]]; then
    printf 'Usage: %s [--uninstall]\n' "$0" >&2
    exit 2
fi

for command_name in python3 codex systemctl; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        printf 'Required command was not found: %s\n' "${command_name}" >&2
        exit 1
    fi
done
if ! systemctl --user show-environment >/dev/null 2>&1; then
    printf 'systemd user services are unavailable. Use cron or another user scheduler.\n' >&2
    exit 1
fi

python_path="$(command -v python3)"
codex_path="$(command -v codex)"
mkdir -p -- "${automation_root}/prompts" "${unit_dir}"
install -m 0644 "${script_dir}/memory_core.py" "${automation_root}/memory_core.py"
install -m 0644 "${script_dir}/routine_runner.py" "${automation_root}/routine_runner.py"
install -m 0644 "${script_dir}/validate_vault.py" "${automation_root}/validate_vault.py"
cp -R -- "${plugin_root}/assets/prompts/." "${automation_root}/prompts/"

systemd_escape() {
    local value="$1"
    value="${value//%/%%}"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    printf '%s' "${value}"
}

python_unit="$(systemd_escape "${python_path}")"
runner_unit="$(systemd_escape "${automation_root}/routine_runner.py")"
codex_unit="$(systemd_escape "${codex_path}")"
working_unit="$(systemd_escape "${automation_root}")"

write_service() {
    local destination="$1"
    local routine="$2"
    local description="$3"
    cat >"${destination}" <<EOF
[Unit]
Description=${description}
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory="${working_unit}"
ExecStart="${python_unit}" "${runner_unit}" ${routine} --codex "${codex_unit}"
NoNewPrivileges=true
EOF
}

write_timer() {
    local destination="$1"
    local service="$2"
    local schedule="$3"
    local description="$4"
    cat >"${destination}" <<EOF
[Unit]
Description=${description}

[Timer]
OnCalendar=${schedule}
Persistent=true
Unit=${service}

[Install]
WantedBy=timers.target
EOF
}

write_service "${unit_dir}/${weekly_service}" weekly "Create one evidence-backed Obsidian project brief per ISO week"
write_service "${unit_dir}/${monthly_service}" monthly "Run one non-destructive Obsidian memory audit per month"
write_timer "${unit_dir}/${weekly_timer}" "${weekly_service}" '*-*-* 09:00:00' "Check the weekly Obsidian project brief"
write_timer "${unit_dir}/${monthly_timer}" "${monthly_service}" '*-*-* 09:15:00' "Check the monthly Obsidian memory audit"

systemctl --user daemon-reload
systemctl --user enable --now "${weekly_timer}" "${monthly_timer}"
printf 'automation_installed=true\nweekly_timer=%s\nmonthly_timer=%s\n' "${weekly_timer}" "${monthly_timer}"
