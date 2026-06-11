#! /bin/bash
source /opt/bash_profile
if [[ -f "$1" ]]; then
  script="$1"; shift
  bash "$script" "$@"
else
  shift
  eval "$@"
fi
