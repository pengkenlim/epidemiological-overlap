"""
Address_epiOverlap_test.py.

Description:
    Unit tests for the address epidemiological overlap workflow.

Author:
    Peng Ken Lim

Date updated:
    2026-09-11
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from tools.Address_epiOverlap import parse_patient_address


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "tools" / "Address_epiOverlap.py"
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


def _run_script_for_variant(variant_path: Path, inputs_dir: Path, output_dir: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--isolate_DOC",
            str(variant_path),
            "--isolate_patient_mapping",
            str(inputs_dir / "Isolate-patient_ID_mapping.tsv"),
            "--patient_address",
            str(inputs_dir / "Patient_addresses.tsv"),
            "--isolate_pairs",
            str(inputs_dir / "Recipient-donor_isolate_pairs.tsv"),
            "--output_folder",
            str(output_dir),
        ],
        cwd=str(REPO_ROOT),
        check=True,
    )


def test_parse_patient_address_accepts_explicit_column_order(tmp_path: Path) -> None:
    input_path = tmp_path / "Patient_addresses_custom_order.tsv"
    input_path.write_text(
        "Row_ID\tPatient_ID\tUnit_number\tPostal_code\tOther\n"
        "1\tPID101\t05-07\t123456\tunused\n"
        "2\tPID102\t3-110\t654321\tunused\n",
        encoding="utf-8",
    )

    parsed = parse_patient_address(str(input_path) + "[2,4,3,1]")

    assert parsed["PID101"] == ("123456", "05-07", "1")
    assert parsed["PID102"] == ("654321", "3-110", "2")


def test_demo_dataset_matches_tracked_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "demo_generated_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    _run_script_for_variant(
        DEMO_INPUTS_DIR / "Isolate_DOC_decimal.tsv",
        DEMO_INPUTS_DIR,
        output_dir,
    )

    generated_events = _read_rows_as_set(output_dir / "Address_epiOverlap_events.tsv")
    expected_events = _read_rows_as_set(DEMO_OUTPUTS_DIR / "Address_epiOverlap_events.tsv")
    assert generated_events == expected_events

    generated_status = _read_rows_as_set(
        output_dir / "Address_epiOverlap_statuses_all_pairs.tsv"
    )
    expected_status = _read_rows_as_set(
        DEMO_OUTPUTS_DIR / "Address_epiOverlap_statuses_all_pairs.tsv"
    )
    assert generated_status == expected_status

    assert any(
        row[0] == "ISO201" and row[1] == "ISO203" for row in generated_status
    )
    assert any(
        row[0] == "POSTCODE" and row[1] == "PID102" and row[2] == "PID105"
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
    )

    generated_events = _read_rows_as_set(output_dir / "Address_epiOverlap_events.tsv")
    expected_events = _read_rows_as_set(REAL_OUTPUTS_DIR / "Address_epiOverlap_events.tsv")
    assert generated_events == expected_events

    generated_status = _read_rows_as_set(
        output_dir / "Address_epiOverlap_statuses_all_pairs.tsv"
    )
    expected_status = _read_rows_as_set(
        REAL_OUTPUTS_DIR / "Address_epiOverlap_statuses_all_pairs.tsv"
    )
    assert generated_status == expected_status


@pytest.mark.parametrize(
    "variant_path",
    sorted((REAL_INPUTS_DIR / "date_format_variants").glob("Isolate_DOC*.tsv")),
    ids=lambda p: p.name,
)
def test_address_epi_overlap_matches_expected_output_for_each_real_doc_variant(
    tmp_path: Path,
    variant_path: Path,
) -> None:
    if not REAL_INPUTS_DIR.exists() or not REAL_OUTPUTS_DIR.exists():
        pytest.skip("Real dataset not available in this workspace.")

    output_dir = tmp_path / variant_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    _run_script_for_variant(variant_path, REAL_INPUTS_DIR, output_dir)

    generated_events = _read_rows_as_set(output_dir / "Address_epiOverlap_events.tsv")
    expected_events = _read_rows_as_set(REAL_OUTPUTS_DIR / "Address_epiOverlap_events.tsv")
    assert generated_events == expected_events

    generated_status = _read_rows_as_set(
        output_dir / "Address_epiOverlap_statuses_all_pairs.tsv"
    )
    expected_status = _read_rows_as_set(
        REAL_OUTPUTS_DIR / "Address_epiOverlap_statuses_all_pairs.tsv"
    )
    assert generated_status == expected_status
