#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_WINDOWS_REPORT_DIR = Path(
    "/mnt/c/Users/olino/Desktop/radix8-reports"
)

DEFAULT_WINDOWS_LAYOUT_DIR = Path(
    "/mnt/c/Users/olino/Desktop/radix8-layouts"
)


def latest_asic_run() -> Path | None:
    """
    Return the newest LibreLane Radix-2 RUN_* directory.
    """

    runs_dir = ROOT / "asic" / "radix2" / "runs"

    if not runs_dir.exists():
        return None

    runs = sorted(
        p
        for p in runs_dir.glob("RUN_*")
        if p.is_dir()
    )

    if not runs:
        return None

    return runs[-1]


def copy_file(
    src: Path,
    dst: Path,
) -> None:
    """
    Copy one file while creating its destination directory.
    """

    dst.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        src,
        dst,
    )


def export_reports() -> bool:
    """
    Export generated HTML reports to the Windows shared directory.
    """

    site = ROOT / "reports" / "site"

    destination = Path(
        os.environ.get(
            "WINDOWS_REPORT_DIR",
            str(DEFAULT_WINDOWS_REPORT_DIR),
        )
    )

    if not site.exists():
        print(
            "ERROR: reports/site does not exist.\n"
            "Run `make report` first."
        )
        return False

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        shutil.copytree(
            site,
            destination,
            dirs_exist_ok=True,
        )

    except OSError as exc:
        print(
            f"ERROR: unable to export reports to Windows:\n"
            f"  {exc}"
        )
        return False

    readme = destination / "README.txt"

    try:
        readme.write_text(
            "Radix-n Divider Thesis EDA/DV reports\n"
            "\n"
            "Open index.html in a browser.\n",
            encoding="utf-8",
        )
    except OSError:
        pass

    print(
        f"Reports exported to: {destination}"
    )

    return True


def collect_physical_files(
    run: Path,
    destination: Path,
) -> int:
    """
    Copy important physical-design artifacts from one LibreLane run.

    The directory hierarchy under final/ is preserved.
    """

    copied = 0

    wanted_suffixes = {
        ".gds",
        ".def",
        ".odb",
        ".lef",
        ".sdc",
        ".spef",
    }

    final_dir = run / "final"

    if final_dir.exists():

        for src in final_dir.rglob("*"):

            if not src.is_file():
                continue

            if src.suffix.lower() not in wanted_suffixes:
                continue

            relative = src.relative_to(final_dir)

            dst = (
                destination
                / "final"
                / relative
            )

            copy_file(
                src,
                dst,
            )

            copied += 1

    # LibreLane KLayout stream-out GDS.
    streamout_gds = sorted(
        run.glob(
            "*-klayout-streamout/*.gds"
        )
    )

    if streamout_gds:

        src = streamout_gds[-1]

        dst = (
            destination
            / "radix2_divider.klayout.gds"
        )

        copy_file(
            src,
            dst,
        )

        copied += 1

    # Compact physical baseline documentation.
    baseline = (
        ROOT
        / "results"
        / "radix2_physical_baseline.md"
    )

    if baseline.exists():

        copy_file(
            baseline,
            destination
            / baseline.name,
        )

        copied += 1

    # Record exactly which LibreLane run produced these files.
    try:
        (
            destination
            / "_SOURCE_RUN.txt"
        ).write_text(
            str(run) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass

    return copied


def export_layout() -> bool:
    """
    Export the newest Radix-2 physical implementation.

    Strategy:

    1. Always export to a unique archive/RUN_* directory first.
    2. Never delete the Windows 'latest' directory.
    3. Try to update latest in-place.
    4. If Windows has a file locked (for example KLayout), keep the
       archived copy and issue a warning rather than failing thesis-run.
    """

    run = latest_asic_run()

    if run is None:
        print(
            "ERROR: no LibreLane Radix-2 RUN_* directory found."
        )
        return False

    base = Path(
        os.environ.get(
            "WINDOWS_LAYOUT_DIR",
            str(DEFAULT_WINDOWS_LAYOUT_DIR),
        )
    )

    radix_dir = (
        base
        / "radix2"
    )

    archive_dir = (
        radix_dir
        / "archive"
        / run.name
    )

    latest_dir = (
        radix_dir
        / "latest"
    )

    radix_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # 1. Archive first.
    #
    # This directory is unique per physical run and therefore
    # should not collide with files currently open in KLayout.
    # ---------------------------------------------------------

    archive_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:

        copied = collect_physical_files(
            run,
            archive_dir,
        )

    except OSError as exc:

        print(
            "ERROR: could not create archived "
            "physical-design export:"
        )

        print(
            f"  {exc}"
        )

        return False

    if copied == 0:

        print(
            f"ERROR: no physical files found in {run}"
        )

        return False

    print(
        f"Archived layout exported to: "
        f"{archive_dir}"
    )

    print(
        f"Physical files archived: {copied}"
    )

    # ---------------------------------------------------------
    # 2. Best-effort latest/ update.
    #
    # IMPORTANT:
    # Do NOT shutil.rmtree(latest_dir).
    #
    # Windows can lock GDS files while KLayout has them open.
    # Deleting the whole directory causes PermissionError.
    # ---------------------------------------------------------

    latest_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    latest_updated = True

    try:

        shutil.copytree(
            archive_dir,
            latest_dir,
            dirs_exist_ok=True,
        )

    except PermissionError as exc:

        latest_updated = False

        print()
        print(
            "WARNING: Windows prevented the "
            "'latest' layout directory from being updated."
        )

        print(
            "This usually means KLayout or another Windows "
            "program currently has one of the files open."
        )

        print()
        print(
            f"Windows/WSL error:\n  {exc}"
        )

        print()
        print(
            "The archived layout is safe and complete:"
        )

        print(
            f"  {archive_dir}"
        )

        print()
        print(
            "Close KLayout and run:"
        )

        print(
            "  make export-layout"
        )

    except OSError as exc:

        latest_updated = False

        print()
        print(
            "WARNING: latest layout could not be refreshed:"
        )

        print(
            f"  {exc}"
        )

        print()
        print(
            "The archive export remains available:"
        )

        print(
            f"  {archive_dir}"
        )

    if latest_updated:

        print(
            f"Latest layout exported to: "
            f"{latest_dir}"
        )

    # Success is based on the immutable archived copy.
    #
    # A locked convenience folder must NOT invalidate an
    # otherwise successful ASIC/thesis run.
    return True


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Export Radix-n thesis HTML reports "
            "and physical-design artifacts to Windows."
        )
    )

    parser.add_argument(
        "--reports",
        action="store_true",
        help="Export HTML reports.",
    )

    parser.add_argument(
        "--layout",
        action="store_true",
        help="Export latest physical layout.",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Export reports and layout.",
    )

    args = parser.parse_args()

    if not (
        args.reports
        or args.layout
        or args.all
    ):
        args.all = True

    ok = True

    if args.reports or args.all:

        ok = (
            export_reports()
            and ok
        )

    if args.layout or args.all:

        ok = (
            export_layout()
            and ok
        )

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
