#!/usr/bin/env bash
set -euo pipefail

# Find duplicate files across two Nextcloud trees by content hash.
SRC_A="${1:-/opt/nextcloud-data}"
SRC_B="${2:-/opt/nextcloud-data-scp}"
OUT_DIR="${3:-/tmp}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script must run as root. Re-launching with sudo..."
  exec sudo "$0" "$SRC_A" "$SRC_B" "$OUT_DIR"
fi

if [[ ! -d "$SRC_A" ]]; then
  echo "Directory not found: $SRC_A" >&2
  exit 1
fi

if [[ ! -d "$SRC_B" ]]; then
  echo "Directory not found: $SRC_B" >&2
  exit 1
fi

HASHES="$OUT_DIR/nextcloud_dupes_hashes.txt"
REPORT="$OUT_DIR/nextcloud_dupes_report.txt"
PAIRS="$OUT_DIR/nextcloud_dupes_pairs.tsv"
ACTIONABLE_REPORT="$OUT_DIR/nextcloud_dupes_actionable_report.txt"
ACTIONABLE_PAIRS="$OUT_DIR/nextcloud_dupes_actionable_pairs.tsv"

command -v sha256sum >/dev/null 2>&1 || {
  echo "sha256sum is required but not installed." >&2
  exit 1
}

command -v find >/dev/null 2>&1 || {
  echo "find is required but not installed." >&2
  exit 1
}

command -v awk >/dev/null 2>&1 || {
  echo "awk is required but not installed." >&2
  exit 1
}

echo "Scanning files in:"
echo "  - $SRC_A"
echo "  - $SRC_B"
echo "Generating full and actionable reports"

tmp_hashes="$(mktemp)"
trap 'rm -f "$tmp_hashes"' EXIT

find "$SRC_A" "$SRC_B" -type f -print0 \
  | xargs -0 sha256sum \
  | sort -k1,1 > "$tmp_hashes"

mv "$tmp_hashes" "$HASHES"

awk '
{
  h=$1
  $1=""
  sub(/^ /,"")
  c[h]++
  paths[h]=paths[h] ORS $0
}
END{
  for (h in c) {
    if (c[h] > 1) {
      print "HASH\t" h "\tCOUNT\t" c[h]
      n=split(paths[h], a, ORS)
      for (i=1; i<=n; i++) if (a[i]!="") print a[i]
      print ""
    }
  }
}
' "$HASHES" > "$REPORT"

awk '
{
  h=$1
  $1=""
  sub(/^ /,"")
  lines[h]=lines[h] ORS h "\t" $0
  c[h]++
}
END{
  for (h in c) if (c[h]>1) {
    n=split(lines[h], a, ORS)
    for (i=1; i<=n; i++) if (a[i]!="") print a[i]
  }
}
' "$HASHES" > "$PAIRS"

awk '
function is_noise(path) {
  return path ~ /\/appdata_[^/]+\// || \
         path ~ /\/preview\// || \
         path ~ /\/files_versions\// || \
         path ~ /\.part$/ || \
         path ~ /\.ocTransferId[0-9]+\.part$/
}
{
  h=$1
  $1=""
  sub(/^ /, "")
  if (is_noise($0)) next
  c[h]++
  lines[h]=lines[h] ORS h "\t" $0
}
END{
  for (h in c) if (c[h] > 1) {
    n=split(lines[h], a, ORS)
    for (i=1; i<=n; i++) if (a[i] != "") print a[i]
  }
}
' "$HASHES" > "$ACTIONABLE_PAIRS"

awk '
{
  h=$1
  $1=""
  sub(/^ /,"")
  c[h]++
  paths[h]=paths[h] ORS $0
}
END{
  for (h in c) {
    if (c[h] > 1) {
      print "HASH\t" h "\tCOUNT\t" c[h]
      n=split(paths[h], a, ORS)
      for (i=1; i<=n; i++) if (a[i]!="") print a[i]
      print ""
    }
  }
}
' "$ACTIONABLE_PAIRS" > "$ACTIONABLE_REPORT"

TOTAL_FILES=$(wc -l < "$HASHES")
DUP_GROUPS=$(grep -c "^HASH" "$REPORT" || true)
DUP_FILES=$(awk '/^HASH\t/{sum+=$4} END{print sum+0}' "$REPORT")
ACTIONABLE_DUP_GROUPS=$(grep -c "^HASH" "$ACTIONABLE_REPORT" || true)
ACTIONABLE_DUP_FILES=$(awk '/^HASH\t/{sum+=$4} END{print sum+0}' "$ACTIONABLE_REPORT")

echo
echo "TOTAL_FILES=$TOTAL_FILES"
echo "DUP_GROUPS=$DUP_GROUPS"
echo "DUP_FILES=$DUP_FILES"
echo "REPORT=$REPORT"
echo "PAIRS=$PAIRS"
echo "ACTIONABLE_DUP_GROUPS=$ACTIONABLE_DUP_GROUPS"
echo "ACTIONABLE_DUP_FILES=$ACTIONABLE_DUP_FILES"
echo "ACTIONABLE_REPORT=$ACTIONABLE_REPORT"
echo "ACTIONABLE_PAIRS=$ACTIONABLE_PAIRS"
echo
echo "Preview (first 20 duplicate groups):"
awk 'BEGIN{g=0} /^HASH\t/{g++; if(g>20) exit} {print}' "$REPORT"
echo
echo "Actionable preview (first 20 duplicate groups):"
awk 'BEGIN{g=0} /^HASH\t/{g++; if(g>20) exit} {print}' "$ACTIONABLE_REPORT"
