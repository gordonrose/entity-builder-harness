#!/usr/bin/env bash

# agentic-script:
#   owner: 00.chat
#   purpose: Provide canonical chat session id and commit log path helper functions.
#   domain: session-log
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/session-log/read-current-chat-log/script.sh
#     - scripts/00.chat/session-log/update-chat-log/script.sh
#     - .agentic/shared/gates/assert_chat_session.sh
#   effects: read-only

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

  sed -n '/<!-- agentic-session/,/-->/p' "$log_file" \
    | sed '/<!-- agentic-session/d;/-->/d' \
    | sed -n "s/^${key}: //p" \
    | head -n 1
}

chat_log_file_for_session_by_metadata() {
  local session_id="$1"
  local branch="chat/${session_id}"
  local grouped_parent found_file found_count file

  grouped_parent="$(chat_log_grouped_dir_for_session "$session_id")"
  grouped_parent="${grouped_parent%/*}"
  found_file=""
  found_count=0

  if [ -d "$grouped_parent" ]; then
    while IFS= read -r file; do
      if [ "$(chat_log_metadata_value "$file" "id")" = "$session_id" ] \
        || [ "$(chat_log_metadata_value "$file" "branch")" = "$branch" ]; then
        found_file="$file"
        found_count=$((found_count + 1))
      fi
    done < <(find "$grouped_parent" -mindepth 2 -maxdepth 2 -type f -name README.md | sort)
  fi

  if [ "$found_count" -eq 1 ]; then
    printf '%s\n' "$found_file"
    return 0
  fi

  return 1
}

chat_log_file_for_session() {
  local session_id="$1"
  local grouped_dir flat_file metadata_file

  grouped_dir="$(chat_log_grouped_dir_for_session "$session_id")"
  flat_file="commitLogs/${session_id}/README.md"

  if [ -f "${grouped_dir}/README.md" ]; then
    printf '%s\n' "${grouped_dir}/README.md"
  elif [ -f "$flat_file" ]; then
    printf '%s\n' "$flat_file"
  elif metadata_file="$(chat_log_file_for_session_by_metadata "$session_id")"; then
    printf '%s\n' "$metadata_file"
  else
    printf '%s\n' "${grouped_dir}/README.md"
  fi
}

chat_log_dir_for_session() {
  local session_id="$1"
  local log_file

  log_file="$(chat_log_file_for_session "$session_id")"
  printf '%s\n' "${log_file%/README.md}"
}
