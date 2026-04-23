#!/usr/bin/env bash

set -euo pipefail

repo_root="$(CDPATH= cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"

assert_eq() {
    local expected="$1"
    local actual="$2"
    local message="$3"

    if [[ "${expected}" != "${actual}" ]]; then
        printf 'FAIL: %s\nexpected: %s\nactual:   %s\n' "${message}" "${expected}" "${actual}" >&2
        exit 1
    fi
}

tmpdir="$(mktemp -d)"
loader="$(mktemp)"
trap 'rm -rf "${tmpdir}"; rm -f "${loader}"' EXIT

awk '/^BACKUP_DIR=/{exit} {print}' "${repo_root}/install.sh" > "${loader}"
# shellcheck disable=SC1090
source "${loader}"

touch "${tmpdir}/LDO_Leviathan_v1.2.cfg"
touch "${tmpdir}/BTT_Manta_M8P_v1.1.cfg"
touch "${tmpdir}/MY-OWN-CUSTOM-TEMPLATE.cfg"

entries=()
while IFS= read -r entry; do
    entries+=("${entry}")
done < <(build_template_menu_entries "${tmpdir}")

assert_eq 3 "${#entries[@]}" "expected one menu entry per template file"
assert_eq "BTT Manta M8P v1.1	${tmpdir}/BTT_Manta_M8P_v1.1.cfg" "${entries[0]}" "entries should be sorted by human-readable label"
assert_eq "LDO Leviathan v1.2	${tmpdir}/LDO_Leviathan_v1.2.cfg" "${entries[1]}" "underscores should be rendered as spaces"
assert_eq "My Own Custom Template	${tmpdir}/MY-OWN-CUSTOM-TEMPLATE.cfg" "${entries[2]}" "special template should get title-cased output"

template_categories=()
while IFS= read -r category; do
    template_categories+=("${category}")
done < <(find "${repo_root}/user_templates/mcu_defaults" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)
assert_eq "expander main mmu toolhead" "${template_categories[*]}" "expected installer coverage for every MCU template category"

for category in "${template_categories[@]}"; do
    if ! grep -q "mcu_defaults/${category}" "${repo_root}/install.sh"; then
        printf 'FAIL: installer does not reference mcu_defaults/%s\n' "${category}" >&2
        exit 1
    fi
done

if grep -q 'mcu_defaults/expand"' "${repo_root}/install.sh"; then
    printf 'FAIL: installer still references stale mcu_defaults/expand path\n' >&2
    exit 1
fi

printf 'ok\n'
