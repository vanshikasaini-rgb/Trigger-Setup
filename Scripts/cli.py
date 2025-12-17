# cli.py
# Command-line orchestrator for Media Portfolio Automation
# CLOUD-NATIVE VERSION (Drive + S3 only)

import argparse

from .refs_manager import phase1_build_refs
from .rekog_manager import index_faces_and_record
from .folders_manager import create_output_structure
from .sorter import phase4_sort_uploads


def run_full_indexing():
    """
    Phase 1 + Phase 2 + Phase 3
    - Build reference images (Drive → S3)
    - Index faces (S3 → Rekognition → Sheet)
    - Create Drive output folders
    """
    phase1_build_refs()
    index_faces_and_record(update_sheet=True)
    create_output_structure()


def run_sorting():
    """
    Phase 4 + Phase 5
    - Read upload folders from Validation sheet
    - Match faces
    - Copy images into student folders
    - Append report to Uploaded Data sheet
    """
    phase4_sort_uploads()


def main():
    parser = argparse.ArgumentParser(
        description="Media Portfolio Automation (Cloud-native)"
    )

    parser.add_argument(
        "--run-index",
        action="store_true",
        help="Run indexing (Phase 1–3): refs, Rekognition, folders"
    )

    parser.add_argument(
        "--run-sort",
        action="store_true",
        help="Run sorting (Phase 4–5): process uploads & report"
    )

    parser.add_argument(
        "--run-all-once",
        action="store_true",
        help="Run full pipeline once (index + sort)"
    )

    args = parser.parse_args()

    if args.run_index:
        run_full_indexing()

    if args.run_sort:
        run_sorting()

    if args.run_all_once:
        run_full_indexing()
        run_sorting()


if __name__ == "__main__":
    main()
