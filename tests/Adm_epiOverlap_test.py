"""
Adm_epiOverlap_test.py.

Description:
    Regression tests for the admission epidemiological overlap workflow.
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
SCRIPT_PATH = REPO_ROOT / "tools" / "Adm_epiOverlap.py"
DEMO_INPUTS_DIR = REPO_ROOT / "data" / "demo" / "inputs"
DEMO_OUTPUTS_DIR = REPO_ROOT / "data" / "demo" / "outputs"
REAL_INPUTS_DIR = REPO_ROOT / "data" / "real" / "inputs"
REAL_OUTPUTS_DIR = REPO_ROOT / "data" / "real" / "outputs"
REAL_ADMISSION_EVENTS_REFERENCE = REAL_OUTPUTS_DIR / "Adm_epiOverlap_events.tsv"
REAL_ADMISSION_STATUS_REFERENCE = REAL_OUTPUTS_DIR / "Adm_epiOverlap_statuses_all_pairs.tsv"


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
            if stripped.startswith("Hospital_Overlap_event_type") or stripped.startswith("Recip_isolate_ID"):
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

    generated_events = _read_rows_as_set(output_dir / "Adm_epiOverlap_events.tsv")
    expected_events = _read_rows_as_set(DEMO_OUTPUTS_DIR / "Adm_epiOverlap_events.tsv")
    assert generated_events == expected_events

    generated_status = _read_rows_as_set(output_dir / "Adm_epiOverlap_statuses_all_pairs.tsv")
    expected_status = _read_rows_as_set(DEMO_OUTPUTS_DIR / "Adm_epiOverlap_statuses_all_pairs.tsv")
    assert generated_status == expected_status

    assert any(
        row[0] == "Hospital Indirect" and row[3] == "PID108" and row[4] == "ISO208"
        for row in generated_events
    )
    assert any(
        row[0] == "No Hospital Contact" and row[3] == "PID110" and row[4] == "ISO210"
        for row in generated_events
    )


def test_real_dataset_matches_local_reference_if_available(tmp_path: Path) -> None:
    assert REAL_INPUTS_DIR.exists(), "Real input directory is not present locally."
    assert REAL_ADMISSION_EVENTS_REFERENCE.exists(), "Real admission event reference is not present locally."
    assert REAL_ADMISSION_STATUS_REFERENCE.exists(), "Real admission status reference is not present locally."

    output_dir = tmp_path / "real_generated_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    _run_script_for_variant(
        REAL_INPUTS_DIR / "Isolate_DOC_decimal.tsv",
        REAL_INPUTS_DIR,
        output_dir,
        decimal_output=True,
    )

    generated_events = _read_rows_as_set(output_dir / "Adm_epiOverlap_events.tsv")
    expected_events = _read_rows_as_set(REAL_ADMISSION_EVENTS_REFERENCE)
    assert generated_events == expected_events

    generated_status = _read_rows_as_set(output_dir / "Adm_epiOverlap_statuses_all_pairs.tsv")
    expected_status = _read_rows_as_set(REAL_ADMISSION_STATUS_REFERENCE)
    assert generated_status == expected_status
