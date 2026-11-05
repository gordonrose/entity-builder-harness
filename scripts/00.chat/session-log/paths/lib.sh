#!/usr/bin/env bash

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.session-log.paths.lib
#   version: 1
#   status: active
#   created_on: "2026-06-15"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Provide canonical chat session id and commit log path helper functions.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.read-current-chat-log
#     path: scripts/00.chat/session-log/read-current-chat-log/script.sh
#   - id: chat.script.session-log.update-chat-log
#     path: scripts/00.chat/session-log/update-chat-log/script.sh
#   effects:
#   - read-only
chat_session_id_from_branch() {
  local branch="$1"

  case "$branch" in
    chat/*)
      printf '%s\n' "${branch#chat/}"
      ;;
    *)
      return 1
      ;;
  esac
}

chat_log_month_name() {
  case "$1" in
    01) printf 'jan\n' ;;
    02) printf 'feb\n' ;;
    03) printf 'mar\n' ;;
    04) printf 'apr\n' ;;
    05) printf 'may\n' ;;
    06) printf 'jun\n' ;;
    07) printf 'jul\n' ;;
    08) printf 'aug\n' ;;
    09) printf 'sep\n' ;;
    10) printf 'oct\n' ;;
    11) printf 'nov\n' ;;
    12) printf 'dec\n' ;;
    *) return 1 ;;
  esac
}

chat_log_grouped_dir_for_session() {
  local session_id="$1"
  local year month day month_name

  year="${session_id:0:4}"
  month="${session_id:5:2}"
  day="${session_id:8:2}"

  if ! month_name="$(chat_log_month_name "$month")"; then
    return 1
  fi

  printf 'commitLogs/%s/%s/%s/%s\n' "$year" "$month_name" "$day" "$session_id"
}

chat_log_metadata_value() {
  local log_file="$1"
  local key="$2"

  # One reader preserves an I/O failure even when the caller disables errexit.
  if ! awk -v key="$key" '
    /<!-- agentic-session/ { inside = 1; next }
    /-->/ { inside = 0; next }
    inside && !printed && index($0, key ": ") == 1 {
      print substr($0, length(key) + 3); printed = 1
    }
  ' "$log_file" 2>/dev/null; then
    printf 'ERROR: session-metadata-read-failed\n' >&2
    return 2
  fi
}

chat_log_file_for_session_by_metadata() {
  local session_id="$1"
  local branch="chat/${session_id}"
  local grouped_parent found_file found_count file files recorded_id recorded_branch

  grouped_parent="$(chat_log_grouped_dir_for_session "$session_id")" || { printf 'ERROR: session-date-invalid\n' >&2; return 2; }
  grouped_parent="${grouped_parent%/*}"
  found_file=""
  found_count=0

  if [ -d "$grouped_parent" ]; then
    files="$(find "$grouped_parent" -mindepth 2 -maxdepth 2 -type f -name README.md 2>/dev/null)" || { printf 'ERROR: session-directory-read-failed\n' >&2; return 2; }
    while IFS= read -r file; do
      [ -n "$file" ] || continue
      recorded_id="$(chat_log_metadata_value "$file" "id")" || return 2
      recorded_branch="$(chat_log_metadata_value "$file" "branch")" || return 2
      if [ "$recorded_id" = "$session_id" ] || [ "$recorded_branch" = "$branch" ]; then
        found_file="$file"
        found_count=$((found_count + 1))
      fi
    done <<< "$files"
  fi

  if [ "$found_count" -eq 1 ]; then
    printf '%s\n' "$found_file"
    return 0
  fi

  # Only a successful scan with no match means absence. Ambiguity is not absence.
  [ "$found_count" -eq 0 ] && return 1
  printf 'ERROR: session-log-ambiguous\n' >&2
  return 2
}

chat_log_file_for_session() {
  local session_id="$1"
  local grouped_dir flat_file metadata_file lookup_status

  grouped_dir="$(chat_log_grouped_dir_for_session "$session_id")" || { printf 'ERROR: session-date-invalid\n' >&2; return 2; }
  flat_file="commitLogs/${session_id}/README.md"

  if [ -f "${grouped_dir}/README.md" ]; then
    printf '%s\n' "${grouped_dir}/README.md"
  elif [ -f "$flat_file" ]; then
    printf '%s\n' "$flat_file"
  elif metadata_file="$(chat_log_file_for_session_by_metadata "$session_id")"; then
    printf '%s\n' "$metadata_file"
  else
    lookup_status=$?
    [ "$lookup_status" -eq 1 ] || return "$lookup_status"
    printf '%s\n' "${grouped_dir}/README.md"
  fi
}

chat_log_dir_for_session() {
  local session_id="$1"
  local log_file

  log_file="$(chat_log_file_for_session "$session_id")" || return $?
  printf '%s\n' "${log_file%/README.md}"
}
