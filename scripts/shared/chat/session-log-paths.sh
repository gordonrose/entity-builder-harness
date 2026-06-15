#!/usr/bin/env bash

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

chat_log_file_for_session() {
  local session_id="$1"
  local grouped_dir flat_file

  grouped_dir="$(chat_log_grouped_dir_for_session "$session_id")"
  flat_file="commitLogs/${session_id}/README.md"

  if [ -f "${grouped_dir}/README.md" ]; then
    printf '%s\n' "${grouped_dir}/README.md"
  elif [ -f "$flat_file" ]; then
    printf '%s\n' "$flat_file"
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
