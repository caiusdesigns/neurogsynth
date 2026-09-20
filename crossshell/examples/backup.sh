#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-./data}"
destination="${2:-./archives}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$destination/backup-$timestamp.tar.gz"

mkdir -p "$destination"
trap 'printf "Backup failed\\n" >&2' ERR

find "$source_dir" -type f -not -path '*/.git/*' -print0 \
  | tar --null -czf "$archive" --files-from -

printf 'Created %s\\n' "$archive"

