#!/usr/bin/env python3
import argparse
import os
import sys
from collections import defaultdict

INPUT = "/tmp/nextcloud_dupes_actionable_pairs.tsv"
DEFAULT_OUT_DIR = "/tmp"

T1_PREFIX = "/opt/nextcloud-data/"
T2_PREFIX = "/opt/nextcloud-data-scp/"


def human_size(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def first_existing_size(paths: list[str]) -> int | None:
    for path in paths:
        try:
            return os.path.getsize(path)
        except OSError:
            continue
    return None


def atomic_write_text(path: str, content: str) -> None:
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        handle.write(content)
    os.replace(temp_path, path)


def load_groups(input_path: str) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    with open(input_path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            file_hash, file_path = parts
            groups[file_hash].append(file_path)
    return groups


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Nextcloud cleanup candidate lists.")
    parser.add_argument("--input", default=INPUT, help="Path to actionable pairs TSV")
    parser.add_argument("--output-dir", default=DEFAULT_OUT_DIR, help="Directory where output files are written")
    args = parser.parse_args()

    input_path = args.input
    out_dir = args.output_dir

    out1 = os.path.join(out_dir, "nextcloud_cross_delete_candidates_scp.txt")
    out2 = os.path.join(out_dir, "nextcloud_cross_delete_candidates_scp_detailed.tsv")
    out3 = os.path.join(out_dir, "nextcloud_t1_top100_groups.tsv")
    out4 = os.path.join(out_dir, "nextcloud_t1_top100_delete_candidates.txt")

    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    os.makedirs(out_dir, exist_ok=True)

    if os.geteuid() != 0:
        print("WARNING: running without root privileges.")
        print("Some file sizes may be unreadable; unknown sizes are marked as -1.")

    if not os.access(out_dir, os.W_OK):
        print(f"Output directory is not writable: {out_dir}", file=sys.stderr)
        return 1

    groups = load_groups(input_path)

    cross_groups: list[tuple[str, int, list[str], list[str], list[str]]] = []
    t1_int_groups: list[tuple[int, str, int, int, list[str], list[str]]] = []

    for file_hash, paths in groups.items():
        in_t1 = [p for p in paths if p.startswith(T1_PREFIX)]
        in_t2 = [p for p in paths if p.startswith(T2_PREFIX)]

        if in_t1 and in_t2:
            size = first_existing_size(paths)
            if size is None:
                size = -1
            cross_groups.append((file_hash, size, in_t1, in_t2, paths))
        elif in_t1 and len(paths) > 1:
            size = first_existing_size(paths)
            if size is None:
                size = -1
                reclaimable = -1
            else:
                reclaimable = size * (len(paths) - 1)
            t1_int_groups.append((reclaimable, file_hash, len(paths), size, in_t1, paths))

    # 1) CROSS deletion candidates on scp side
    out1_lines: list[str] = []
    out2_lines: list[str] = ["hash\tsize_bytes\tpath_scp\tpaired_path_data_sample\n"]
    for file_hash, size, in_t1, in_t2, _paths in cross_groups:
        sample_data_path = in_t1[0]
        for path_scp in in_t2:
            out1_lines.append(path_scp + "\n")
            out2_lines.append(f"{file_hash}\t{size}\t{path_scp}\t{sample_data_path}\n")
    atomic_write_text(out1, "".join(out1_lines))
    atomic_write_text(out2, "".join(out2_lines))

    # 2) Top 100 T1 internal groups by reclaimable bytes
    # Known-size groups first by reclaimable bytes, then unknown-size by count.
    t1_int_groups.sort(key=lambda item: (item[0] >= 0, item[0], item[2]), reverse=True)
    top100 = t1_int_groups[:100]

    out3_lines: list[str] = ["rank\thash\tcount\tsize_bytes\treclaimable_bytes\tsample_path\tall_paths_joined_by_pipe\n"]
    for rank, (reclaimable, file_hash, count, size, _in_t1, paths) in enumerate(top100, start=1):
        all_paths = "|".join(paths)
        out3_lines.append(f"{rank}\t{file_hash}\t{count}\t{size}\t{reclaimable}\t{paths[0]}\t{all_paths}\n")
    atomic_write_text(out3, "".join(out3_lines))

    out4_lines: list[str] = []
    for _reclaimable, _file_hash, _count, _size, _in_t1, paths in top100:
        for candidate in paths[1:]:
            out4_lines.append(candidate + "\n")
    atomic_write_text(out4, "".join(out4_lines))

    cross_group_count = len(cross_groups)
    cross_candidate_count = sum(len(in_t2) for _h, _s, _in_t1, in_t2, _p in cross_groups)
    cross_candidate_bytes = sum(size * len(in_t2) for _h, size, _in_t1, in_t2, _p in cross_groups if size >= 0)

    t1_group_count = len(t1_int_groups)
    top100_reclaim = sum(reclaimable for reclaimable, _h, _c, _s, _in_t1, _p in top100 if reclaimable >= 0)

    print(f"CROSS_GROUPS={cross_group_count}")
    print(f"CROSS_SCP_DELETE_CANDIDATES={cross_candidate_count}")
    print(f"CROSS_SCP_CANDIDATE_BYTES={cross_candidate_bytes}")
    print(f"CROSS_SCP_CANDIDATE_BYTES_HUMAN={human_size(cross_candidate_bytes)}")
    print(f"T1_INT_GROUPS={t1_group_count}")
    print(f"T1_TOP100_RECLAIM_BYTES={top100_reclaim}")
    print(f"T1_TOP100_RECLAIM_BYTES_HUMAN={human_size(top100_reclaim)}")
    print(f"OUT1={out1}")
    print(f"OUT2={out2}")
    print(f"OUT3={out3}")
    print(f"OUT4={out4}")
    print("TOP10_BEGIN")
    for rank, (reclaimable, file_hash, count, _size, _in_t1, paths) in enumerate(top100[:10], start=1):
        print(f"{rank}\t{file_hash[:12]}\t{count}\t{human_size(reclaimable)}\t{paths[0]}")
    print("TOP10_END")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
