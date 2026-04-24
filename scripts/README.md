# Nextcloud Deduplication Scripts

Two-step workflow to find and prepare cleanup lists for duplicate files across Nextcloud data directories.

## Prerequisites

- Run as root (or with `sudo`)
- `sha256sum`, `find`, `awk` available on the host
- Python 3.10+ for the second step

## Step 1 — Find duplicates

```bash
sudo bash find_nextcloud_duplicates.sh [SRC_A] [SRC_B] [OUT_DIR]
```

| Argument | Default |
|---|---|
| `SRC_A` | `/opt/nextcloud-data` |
| `SRC_B` | `/opt/nextcloud-data-scp` |
| `OUT_DIR` | `/tmp` |

Hashes every file under both trees with SHA-256 and writes:

| File | Description |
|---|---|
| `nextcloud_dupes_hashes.txt` | Raw `hash  path` list |
| `nextcloud_dupes_report.txt` | Human-readable grouped report |
| `nextcloud_dupes_pairs.tsv` | All duplicate pairs as TSV |
| `nextcloud_dupes_actionable_pairs.tsv` | Same, with noise filtered out (previews, versions, `.part` files) |

## Step 2 — Build cleanup lists

```bash
sudo python3 build_nextcloud_cleanup_lists.py [--input FILE] [--output-dir DIR]
```

| Option | Default |
|---|---|
| `--input` | `/tmp/nextcloud_dupes_actionable_pairs.tsv` |
| `--output-dir` | `/tmp` |

Reads the actionable pairs produced by step 1 and writes four files:

| File | Description |
|---|---|
| `nextcloud_cross_delete_candidates_scp.txt` | One path per line — files in `SRC_B` that already exist in `SRC_A` (safe to delete from the SCP tree) |
| `nextcloud_cross_delete_candidates_scp_detailed.tsv` | Same with hash, size, and the matching `SRC_A` path for verification |
| `nextcloud_t1_top100_groups.tsv` | Top 100 internal duplicate groups inside `SRC_A`, ranked by reclaimable bytes |
| `nextcloud_t1_top100_delete_candidates.txt` | Paths to delete to resolve those top-100 groups (keeps one copy per group) |

A summary is printed to stdout with counts and human-readable sizes.

## Typical run

```bash
# 1. Scan (takes a while on large trees)
sudo bash scripts/find_nextcloud_duplicates.sh

# 2. Build lists
sudo python3 scripts/build_nextcloud_cleanup_lists.py

# 3. Review before deleting
cat /tmp/nextcloud_cross_delete_candidates_scp_detailed.tsv | head -20

# 4. Delete (double-check first!)
xargs -a /tmp/nextcloud_cross_delete_candidates_scp.txt rm -v
```
