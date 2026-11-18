#!/bin/sh
# Full rescan of the Nextcloud Music app library (scheduled weekly via cron).
# A lock prevents overlapping scans if one runs longer than expected.
LOCK_FILE=/tmp/nextcloud-music-scan.lock

flock -n "$LOCK_FILE" -c '
  cd /var/www/html || exit 1
  echo "[music_scan] $(date -Is) starting music:scan --rescan --all"
  timeout 12h php occ music:scan --rescan --all
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "[music_scan] $(date -Is) completed successfully"
  else
    echo "[music_scan] $(date -Is) FAILED (exit $rc)"
  fi
  exit $rc
' 2>/dev/null || echo "[music_scan] skipped (a scan is already running)"
