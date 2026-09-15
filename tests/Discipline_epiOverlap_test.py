"""
Discipline_epiOverlap_test.py.

Description:
    Regression tests for the discipline epidemiological overlap workflow.
    These checks compare the generated outputs against the tracked demo data,
    and against the local real-data reference outputs when available.

Author:
    Peng Ken Lim
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "tools" / "Discipline_epiOverlap.py"
DEMO_INPUTS_DIR = REPO_ROOT / "data" / "demo" / "inputs"
DEMO_OUTPUTS_DIR = REPO_ROOT / "data" / "demo" / "outputs"
REAL_INPUTS_DIR = REPO_ROOT / "data" / "real" / "inputs"
REAL_OUTPUTS_DIR = REPO_ROOT / "data" / "real" / "outputs"


def _normalize_row(line: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in re.split(r"\t+|\s{2,}", line.strip()) if part.strip())


def _read_rows_as_set(path: Path) -> set[tuple[str, ...]]:
    if not path.exists():
        return set()
    rows: set[tuple[str, ...]] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("Overlap_event_type") or stripped.startswith("Recip_isolate_ID"):
                continue
            rows.add(_normalize_row(stripped))
    return rows


def _run_script_for_variant(
    variant_path: Path,
    inputs_dir: Path,
    output_dir: Path,
    *,
    decimal_output: bool = False,
) -> None:
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--isolate_DOC",
        str(variant_path),
        "--isolate_patient_mapping",
        str(inputs_dir / "Isolate-patient_ID_mapping.tsv"),
        "--patient_admission_details",
        str(inputs_dir / "Patient_admission_details.tsv"),
        "--isolate_pairs",
        str(inputs_dir / "Recipient-donor_isolate_pairs.tsv"),
        "--output_folder",
        str(output_dir),
    ]
    if decimal_output:
        command.append("--decimal_date")

    subprocess.run(command, cwd=str(REPO_ROOT), check=True)


def test_demo_dataset_matches_tracked_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "demo_generated_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    _run_script_for_variant(
        DEMO_INPUTS_DIR / "Isolate_DOC_decimal.tsv",
        DEMO_INPUTS_DIR,
        output_dir,
    )

    generated_events = _read_rows_as_set(output_dir / "Discipline_epiOverlap_events.tsv")
    expected_events = _read_rows_as_set(DEMO_OUTPUTS_DIR / "Discipline_epiOverlap_events.tsv")
    assert generated_events == expected_events

    generated_status = _read_rows_as_set(
        output_dir / "Discipline_epiOverlap_statuses_all_pairs.tsv"
    )
    expected_status = _read_rows_as_set(
        DEMO_OUTPUTS_DIR / "Discipline_epiOverlap_statuses_all_pairs.tsv"
    )
    assert generated_status == expected_status

    assert any(
        row[0] == "Discipline Indirect" and row[1] == "PID108" and row[2] == "ISO208"
        for row in generated_events
    )
    assert any(
        row[0] == "No Discipline Contact" and row[1] == "PID110" and row[2] == "ISO210"
        for row in generated_events
    )


def test_real_dataset_matches_local_outputs_if_available(tmp_path: Path) -> None:
    if not REAL_INPUTS_DIR.exists() or not REAL_OUTPUTS_DIR.exists():
        pytest.skip("Real dataset is not present locally, so this check is skipped.")

    output_dir = tmp_path / "real_generated_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    _run_script_for_variant(
        REAL_INPUTS_DIR / "Isolate_DOC_decimal.tsv",
        REAL_INPUTS_DIR,
        output_dir,
        decimal_output=True,
    )

    generated_events = _read_rows_as_set(output_dir / "Discipline_epiOverlap_events.tsv")
    expected_events = _read_rows_as_set(REAL_OUTPUTS_DIR / "Discipline_epiOverlap_events.tsv")
    assert generated_events == expected_events

    generated_status = _read_rows_as_set(
        output_dir / "Discipline_epiOverlap_statuses_all_pairs.tsv"
    )
    expected_status = _read_rows_as_set(
        REAL_OUTPUTS_DIR / "Discipline_epiOverlap_statuses_all_pairs.tsv"
    )
    assert generated_status == expected_status


@pytest.mark.parametrize(
    "variant_path",
    sorted((REAL_INPUTS_DIR / "date_format_variants").glob("Isolate_DOC*.tsv")),
    ids=lambda p: p.name,
)
def test_discipline_epi_overlap_matches_expected_output_for_each_real_doc_variant(
    tmp_path: Path,
    variant_path: Path,
) -> None:
    if not REAL_INPUTS_DIR.exists() or not REAL_OUTPUTS_DIR.exists():
        pytest.skip("Real dataset not available in this workspace.")

    # The repo tracks only one canonical real-data reference output, so we only
    # validate variant inputs when a variant-specific reference file is available.
    variant_reference = REAL_OUTPUTS_DIR / f"{variant_path.stem}_expected.tsv"
    if not variant_reference.exists():
        pytest.skip(f"No expected output is tracked for {variant_path.name}; skipping variant-specific comparison.")

    output_dir = tmp_path / variant_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    _run_script_for_variant(
        variant_path,
        REAL_INPUTS_DIR,
        output_dir,
        decimal_output=True,
    )

    generated_events = _read_rows_as_set(output_dir / "Discipline_epiOverlap_events.tsv")
    expected_events = _read_rows_as_set(variant_reference)
    assert generated_events == expected_events

    generated_status = _read_rows_as_set(
        output_dir / "Discipline_epiOverlap_statuses_all_pairs.tsv"
    )
    expected_status = _read_rows_as_set(
        variant_reference.with_name(variant_reference.name.replace("_events", "_statuses_all_pairs"))
    )
    assert generated_status == expected_status
