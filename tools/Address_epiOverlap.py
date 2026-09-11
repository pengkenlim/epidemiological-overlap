"""
Address_epiOverlap.py.

Description:
    Compute epidemiological overlap of isolate transmission based on patient address data.

Author:
    Peng Ken Lim
    &
    MAI-Code-1.1-Flash

Date updated:
    2026-09-11

Running instructions:
    Create environment (if not already created):
        cd /path/to/epidemiological-overlap/
        python -m venv .venv
        source .venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt

    Activate environment (if not already activated):
        source .venv/bin/activate

    Expected input columns (by position, not by exact header-name match):
        --isolate_DOC:
            Isolate_ID: Column 1
            Date of Culture (DOC): Column 2
            Example rows:
                ISO201    2010-09-06
                ISO202    2010.682192
                ISO203    06/09/2010

        --isolate_patient_mapping:
            Isolate_ID: Column 1
            Patient_ID: Column 2
            Example rows:
                ISO201    PID101
                ISO202    PID102

        --patient_address:
            Patient_ID: Column 1
            Postal code: Column 2
            Unit number: Column 3
            Row Number: Column 4
            Example rows:
                PID101    123456    05-07    6
                PID102    654321    3-110    7

        --isolate_pairs:
            Recip_isolate_ID: Column 1
            Donor_isolate_ID: Column 2
            Example rows:
                ISO301    ISO201
                ISO302    ISO202

    The parser reads these files based on expected column orders and does not require the literal header names to match exactly.
    You can provide files with different header names as long as the column order matches the expected order.
    Additionally, you can specify the columns explicitly (refer to usage information below).

    Command proper:
        python ./tools/Address_epiOverlap.py [options]
        options:
            --isolate_DOC                 Path to the isolate Date-of-culture TSV. Expected column order: 1,2 --> Isolate_ID, Date of Culture (DOC)
            --isolate_patient_mapping     Path to the isolate-to-patient mapping TSV. Expected column order: 1,2 --> Isolate_ID, Patient_ID.
            --patient_address             Path to the patient address TSV. Expected column order: 1,2,3,4 --> Patient_ID, Postal code, Unit number, Row Number.
            --isolate_pairs               Path to the isolate pair TSV. Expected column order: 1,2 --> Recip_isolate_ID, Donor_isolate_ID.
            --output_folder               Path to the output directory for generated TSV files.
            --help                        Show this help message and exit.
        
        additional information:
            You can override the default column order of all input files by specifying the columns explicitly in their corresponding argument flags
            for e.g, 
                ---patient_address /path/to/file.tsv[1,3,2,5]
                implies the following:
                    Column 1 in the file corresponds to Patient_ID
                    Column 3 in the file corresponds to Postal code
                    Column 2 in the file corresponds to Unit number
                    Column 5 in the file corresponds to Row Number
Dependencies:
    - os
    - sys
    - argparse
    - python-dateutil
    - datetime
    - collections
"""

import argparse
import os
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta

from dateutil import parser as date_parser


def infer_slash_date_format(date_values):
    """
    Infer the date ordering used in slash-delimited date strings.

    This helper inspects a column of date values and determines whether the
    slash format is most consistent with dd/mm/yyyy or mm/dd/yyyy.

    Args:
        date_values: Iterable of date strings containing forward-slash separators.

    Returns:
        str | None: The inferred datetime format string, or None when no slash
        dates are present.
    """
    slash_values = [str(value).strip() for value in date_values if "/" in str(value) and str(value).strip()]
    if not slash_values:
        return None

    first_day_like = 0
    first_month_like = 0
    second_day_like = 0
    second_month_like = 0

    for value in slash_values:
        parts = value.split("/")
        if len(parts) != 3:
            continue
        try:
            first, second, _ = map(int, parts)
        except ValueError:
            continue

        if 1 <= first <= 31:
            first_day_like += 1
        if 1 <= first <= 12:
            first_month_like += 1

        if 1 <= second <= 31:
            second_day_like += 1
        if 1 <= second <= 12:
            second_month_like += 1

    if first_month_like > first_day_like:
        return "%m/%d/%Y"
    if first_day_like > first_month_like:
        return "%d/%m/%Y"
    if second_month_like > second_day_like:
        return "%d/%m/%Y"
    if second_day_like > second_month_like:
        return "%m/%d/%Y"
    return "%d/%m/%Y"


def infer_hyphen_date_format(date_values):
    """
    Infer the date ordering used in hyphen-delimited date strings.

    This helper inspects a column of date values and determines whether the
    hyphen format is most consistent with dd-mm-yyyy or mm-dd-yyyy.

    Args:
        date_values: Iterable of date strings containing hyphen separators.

    Returns:
        str | None: The inferred datetime format string, or None when no
        hyphen dates are present.
    """
    hyphen_values = [str(value).strip() for value in date_values if "-" in str(value) and str(value).strip()]
    if not hyphen_values:
        return None

    first_day_like = 0
    first_month_like = 0
    second_day_like = 0
    second_month_like = 0

    for value in hyphen_values:
        parts = value.split("-")
        if len(parts) != 3:
            continue
        try:
            first, second, _ = map(int, parts)
        except ValueError:
            continue

        if 1 <= first <= 31:
            first_day_like += 1
        if 1 <= first <= 12:
            first_month_like += 1

        if 1 <= second <= 31:
            second_day_like += 1
        if 1 <= second <= 12:
            second_month_like += 1

    if first_month_like > first_day_like:
        return "%m-%d-%Y"
    if first_day_like > first_month_like:
        return "%d-%m-%Y"
    if second_month_like > second_day_like:
        return "%d-%m-%Y"
    if second_day_like > second_month_like:
        return "%m-%d-%Y"
    return "%d-%m-%Y"


def parse_date_string(date_str: str, slash_format: str | None = None, hyphen_format: str | None = None):
    """
    Parse a date string from a supported epidemiology input format.

    This helper handles standard ISO-like strings, slash-delimited dates,
    hyphen-delimited dates, natural-language dates, and decimal-year values
    such as 2010.682192.

    Args:
        date_str: Date value as a string from the DOC input file.
        slash_format: Optional explicit slash date format, such as %d/%m/%Y.
        hyphen_format: Optional explicit hyphen date format, such as %d-%m-%Y.

    Returns:
        date | None: Parsed date object, or None when the value cannot be parsed.
    """
    if date_str is None:
        return None

    date_str = str(date_str).strip()
    if date_str.lower() in {"", "n.a", "na", "nan", "null"}:
        return None

    if "/" in date_str:
        if slash_format is not None:
            try:
                return datetime.strptime(date_str, slash_format).date()
            except ValueError:
                pass

        for candidate in ("%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(date_str, candidate).date()
            except ValueError:
                continue

    if "-" in date_str:
        if hyphen_format is not None:
            try:
                return datetime.strptime(date_str, hyphen_format).date()
            except ValueError:
                pass

        for candidate in ("%d-%m-%Y", "%m-%d-%Y"):
            try:
                return datetime.strptime(date_str, candidate).date()
            except ValueError:
                continue

    try:
        parsed = date_parser.parse(date_str)
        if parsed is not None:
            return parsed.date()
    except (TypeError, ValueError):
        pass

    try:
        decimal_year = float(date_str)
        year = int(decimal_year)
        fraction = decimal_year - year
        leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        days_in_year = 366 if leap_year else 365
        day_of_year = int(round(fraction * days_in_year))
        day_of_year = max(1, min(day_of_year, days_in_year))
        return date(year, 1, 1) + timedelta(days=day_of_year - 1)
    except ValueError:
        return None


def build_parser() -> argparse.ArgumentParser:
    """
    Construct the CLI argument parser for the address overlap workflow.

    The parser defines the input paths required for isolate dates, patient
    mapping, patient addresses, isolate pairs, and output generation. It also
    documents the expected column order and optional file-path override syntax
    that allows users to reorder columns without renaming headers.

    Returns:
        argparse.ArgumentParser: Configured parser for the workflow CLI.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Compute epidemiological overlap of isolate transmission based on "
            "patient address data.\n\n"
            "Expected column order (not exact header-name matching):\n"
            "  --isolate_DOC: Isolate_ID, Date of Culture (DOC)\n"
            "  --isolate_patient_mapping: Isolate_ID, Patient_ID\n"
            "  --patient_address: Patient_ID, Postal code, Unit number, Row Number\n"
            "  --isolate_pairs: Recip_isolate_ID, Donor_isolate_ID\n\n"
            "Override column positions per file with syntax like:\n"
            "  --patient_address /path/to/file.tsv[1,3,2,5]"
        )
    )
    parser.add_argument(
        "--isolate_DOC",
        type=str,
        required=True,
        help=(
            "Path to the isolate Date-of-culture TSV. "
            "Expected column order: Isolate_ID, Date of Culture (DOC). "
            "Accepts ISO dates, slash dates, hyphen dates, and decimal-year values. "
            "Optional override: /path/to/file.tsv[2,1]."
        ),
    )
    parser.add_argument(
        "--isolate_patient_mapping",
        type=str,
        required=True,
        help=(
            "Path to the isolate-to-patient mapping TSV. "
            "Expected column order: Isolate_ID, Patient_ID. "
            "Optional override: /path/to/file.tsv[2,1]."
        ),
    )
    parser.add_argument(
        "--patient_address",
        type=str,
        required=True,
        help=(
            "Path to the patient address TSV. "
            "Expected column order: Patient_ID, Postal code, Unit number, Row Number. "
            "Optional override: /path/to/file.tsv[1,3,2,5]."
        ),
    )
    parser.add_argument(
        "--isolate_pairs",
        type=str,
        required=True,
        help=(
            "Path to the isolate pair TSV. "
            "Expected column order: Recip_isolate_ID, Donor_isolate_ID. "
            "Optional override: /path/to/file.tsv[2,1]."
        ),
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        required=True,
        help="Directory where the output TSV files are written.",
    )
    return parser


def _resolve_file_and_column_order(file_path: str) -> tuple[str, list[int] | None]:
    """
    Extract an optional explicit column-order override from a file path.

    The supported syntax is path/to/file.tsv[1,3,2,5], where the bracketed list
    tells the parser which source columns to use in which order.

    Args:
        file_path: Path to the TSV file, optionally followed by a column-order
            override in square brackets.

    Returns:
        tuple[str, list[int] | None]: The real file path and the resolved column
        order if an override was supplied; otherwise the original path and None.
    """
    match = re.fullmatch(r"(.+?)\[(\d+(?:,\d+)*)\]", file_path)
    if match is None:
        return file_path, None

    actual_path = match.group(1)
    indices = [int(part) for part in match.group(2).split(",")]
    for value in indices:
        if value <= 0:
            raise ValueError(f"Column indices must be positive integers: {file_path!r}")
    return actual_path, indices


def _read_tsv_rows(file_path: str, expected_columns: int | None = None):
    """
    Read a TSV file and optionally reorder columns according to a user override.

    Args:
        file_path: Path to the input TSV, optionally ending in a bracketed input
            column-order override.
        expected_columns: Number of columns expected for each row after reordering.

    Returns:
        list[list[str]]: Parsed rows as lists of string values.
    """
    resolved_path, column_order = _resolve_file_and_column_order(file_path)
    with open(resolved_path, "r", encoding="utf-8") as handle:
        rows = []
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split("\t")
            if expected_columns is not None and len(parts) < expected_columns:
                raise ValueError(
                    f"Row in {resolved_path!r} has fewer than {expected_columns} columns: {stripped!r}"
                )
            if column_order is not None:
                if len(column_order) != expected_columns:
                    raise ValueError(
                        f"Column order {column_order} for {resolved_path!r} does not match expected width {expected_columns}."
                    )
                parts = [parts[index - 1] for index in column_order]
            rows.append(parts)
    return rows


def parse_isolate_DOC(file_path: str):
    """
    Parse the isolate date-of-culture input file.

    Supported inputs include decimal-year values such as ``2010.682192`` as
    well as common calendar formats such as ISO dates, slash dates, and text
    dates. When slash dates are present, the format is inferred from the whole
    column before parsing to reduce ambiguity.

    Returns:
        dict[str, date]: Mapping from isolate ID to culture date.
    """
    isolate_DOC_dict = {}
    date_values = []

    rows = _read_tsv_rows(file_path, expected_columns=2)
    for line_idx, row in enumerate(rows):
        if line_idx == 0:
            continue
        isolate_id, date_str = row
        date_str = date_str.strip()
        if date_str.lower() in {"", "n.a", "na", "nan", "null"}:
            continue
        date_values.append(date_str)
        isolate_DOC_dict[isolate_id] = None

    slash_format = infer_slash_date_format(date_values)
    hyphen_format = infer_hyphen_date_format(date_values)

    for line_idx, row in enumerate(rows):
        if line_idx == 0:
            continue
        isolate_id, date_str = row
        date_str = date_str.strip()
        if date_str.lower() in {"", "n.a", "na", "nan", "null"}:
            continue

        parsed_date = parse_date_string(date_str, slash_format=slash_format, hyphen_format=hyphen_format)
        if parsed_date is None:
            raise ValueError(f"Could not parse date for isolate '{isolate_id}': {date_str!r}")

        isolate_DOC_dict[isolate_id] = parsed_date

    return isolate_DOC_dict

def parse_isolate_patient_mapping(file_path: str):
    """
    Parse the isolate-to-patient mapping input file.

    This function reads a TSV file where the first row is a header and
    each subsequent row contains:
        Isolate_ID    Patient_ID

    The returned dictionaries maps each isolate ID to the corresponding
    patient ID and each patient ID to the corresponding isolate IDs (can be more than one).

    Returns:
        dict[str, str]: Mapping from isolate ID to patient ID.
        dict[str, list[str]]: Mapping from patient ID to a list of corresponding isolate IDs.
    """
    isolate_patient_mapping_dict = {}
    patient_isolate_mapping_dict = {}
    rows = _read_tsv_rows(file_path, expected_columns=2)
    for line_idx, row in enumerate(rows):
        if line_idx == 0:
            continue
        isolate_id, patient_id = row
        isolate_patient_mapping_dict[isolate_id] = patient_id
        if patient_id not in patient_isolate_mapping_dict:
            patient_isolate_mapping_dict[patient_id] = []
        patient_isolate_mapping_dict[patient_id].append(isolate_id)
    return isolate_patient_mapping_dict, patient_isolate_mapping_dict

def parse_patient_address(file_path: str):
    """
    Parse the patient address input file.

    This function reads a TSV file where the first row is a header and
    each subsequent row contains:
        Patient_ID  Postal code    Unit number    Row Number

    The returned dictionary maps each patient ID to the corresponding
    postal code, unit number, and row number.

    Returns:
        dict[str, tuple[str, str, str]]: Mapping from patient ID to a tuple containing postal code, unit number, and row number.
    """
    patient_address_dict = {}
    rows = _read_tsv_rows(file_path, expected_columns=4)
    for line_idx, row in enumerate(rows):
        if line_idx == 0:
            continue
        patient_id, postal_code, unit_number, row_number = row
        patient_address_dict[patient_id] = (postal_code, unit_number, row_number)
    return patient_address_dict

def parse_isolate_pairs(file_path: str):
    """
    Parse the isolate pairs input file.

    This function reads a TSV file where the first row is a header and
    each subsequent row contains:
        Isolate_ID_1  Isolate_ID_2
    where Isolate_ID_1 and Isolate_ID_2 are the recipient and donor isolates, respectively.
    The returned dicts map donor isolate IDs to recipient isolate IDs and vice versa.

    Returns:
        dict[str, set[str]]: Mapping from donor isolate ID to a set of recipient isolate IDs.
        dict[str, set[str]]: Mapping from recipient isolate ID to a set of donor isolate IDs.
    """
    isolate_pairs_donorkey = {}
    isolate_pairs_recipientkey = {}
    rows = _read_tsv_rows(file_path, expected_columns=2)
    for line_idx, row in enumerate(rows):
        if line_idx == 0:
            continue
        isolate_id_1, isolate_id_2 = row
        if isolate_id_1 not in isolate_pairs_recipientkey:
            isolate_pairs_recipientkey[isolate_id_1] = set()
        isolate_pairs_recipientkey[isolate_id_1].add(isolate_id_2)

        if isolate_id_2 not in isolate_pairs_donorkey:
            isolate_pairs_donorkey[isolate_id_2] = set()
        isolate_pairs_donorkey[isolate_id_2].add(isolate_id_1)

    return isolate_pairs_donorkey, isolate_pairs_recipientkey

def find_overlap_write_outputfiles(event_outpath, status_outpath,
                             isolate_DOC_dict,
                             isolate_patient_mapping_dict,
                             patient_address_dict,
                             isolate_pairs_donorkey_dict,
                             isolate_pairs_recipientkey_dict):
    """
    Detect address overlaps and write the event and status TSV outputs.

    The function compares recipient-donor isolate pairs, resolves each isolate to
    its patient and address, and writes a tab-delimited event log plus a summary
    status table describing whether postcode and unit-level overlaps occurred.

    Args:
        event_outpath: Output path for the overlap event TSV.
        status_outpath: Output path for the pair-level status TSV.
        isolate_DOC_dict: Mapping of isolate IDs to culture dates.
        isolate_patient_mapping_dict: Mapping of isolate IDs to patient IDs.
        patient_address_dict: Mapping of patient IDs to address fields.
        isolate_pairs_donorkey_dict: Mapping of donor isolate IDs to recipient isolate IDs.
        isolate_pairs_recipientkey_dict: Mapping of recipient isolate IDs to donor isolate IDs.

    Returns:
        None. Output files are written to disk.
    """
    event_outfile_line_contents = [
        "Overlap_event_type\tRecip_patient_ID\tDonor_patient_ID\tRecip_patient_address_hash\tDonor_patient_address_hash"
    ]
    status_outfile_line_contents = [
        "Recip_isolate_ID\tDonor_isolate_ID\tRecip_patient_ID\tDonor_patient_ID\tPostal_code_overlap\tUnit_number_overlap"
    ]

    for donor_isolate_id, recipient_isolate_ids in isolate_pairs_donorkey_dict.items():
        donor_patient_id = isolate_patient_mapping_dict.get(donor_isolate_id)
        for recipient_isolate_id in recipient_isolate_ids:
            recipient_patient_id = isolate_patient_mapping_dict.get(recipient_isolate_id)

            postal_overlap = False
            unit_overlap = False
            if donor_patient_id in patient_address_dict and recipient_patient_id in patient_address_dict:
                if patient_address_dict[donor_patient_id][0] == patient_address_dict[recipient_patient_id][0]:
                    postal_overlap = True
                    recipient_address = " ".join([recipient_patient_id] + list(patient_address_dict[recipient_patient_id]))
                    donor_address = " ".join([donor_patient_id] + list(patient_address_dict[donor_patient_id]))
                    event_outfile_line_contents.append(
                        f"POSTCODE\t{recipient_patient_id}\t{donor_patient_id}\t{recipient_address}\t{donor_address}"
                    )

                    if patient_address_dict[donor_patient_id][1] == patient_address_dict[recipient_patient_id][1]:
                        unit_overlap = True
                        event_outfile_line_contents.append(
                            f"UNIT\t{recipient_patient_id}\t{donor_patient_id}\t{recipient_address}\t{donor_address}"
                        )

            status_outfile_line_contents.append(
                f"{recipient_isolate_id}\t{donor_isolate_id}\t{recipient_patient_id}\t{donor_patient_id}\t{'POSTCODE' if postal_overlap else ''}\t{'UNIT' if unit_overlap else ''}"
            )

    with open(event_outpath, "w", encoding="utf-8") as event_outfile:
        for line in event_outfile_line_contents:
            event_outfile.write(line + "\n")

    with open(status_outpath, "w", encoding="utf-8") as status_outfile:
        for line in status_outfile_line_contents:
            status_outfile.write(line + "\n")


def main() -> int:
    """
    Execute the epidemiological overlap workflow from the command line.

    This function parses the required arguments, loads the input TSV files,
    computes postcode and unit overlaps between pairs of isolates, and writes the
    output files to the requested folder.

    Returns:
        int: Exit code for the CLI command. Returns 0 on successful execution.
    """
    parser = build_parser()
    args = parser.parse_args()

    print("Input arguments:")
    print(f"  isolate_DOC: {args.isolate_DOC}")
    print(f"  isolate_patient_mapping: {args.isolate_patient_mapping}")
    print(f"  patient_address: {args.patient_address}")
    print(f"  isolate_pairs: {args.isolate_pairs}")
    print(f"  output_folder: {args.output_folder}")

    # Parse the input files
    isolate_DOC_dict = parse_isolate_DOC(args.isolate_DOC)
    isolate_patient_mapping_dict, _ = parse_isolate_patient_mapping(args.isolate_patient_mapping)
    patient_address_dict = parse_patient_address(args.patient_address)
    isolate_pairs_donorkey_dict, isolate_pairs_recipientkey_dict = parse_isolate_pairs(args.isolate_pairs)

    os.makedirs(args.output_folder, exist_ok=True)
    event_outpath = os.path.join(args.output_folder, "Address_epiOverlap_events.tsv")
    status_outpath = os.path.join(args.output_folder, "Address_epiOverlap_statuses_all_pairs.tsv")

    with open(os.path.join(args.output_folder, "Address_epiOverlap_Argslog.txt"), "w", encoding="utf-8") as arg_outfile:
        arg_outfile.write(f"isolate_DOC: {args.isolate_DOC}\n")
        arg_outfile.write(f"isolate_patient_mapping: {args.isolate_patient_mapping}\n")
        arg_outfile.write(f"patient_address: {args.patient_address}\n")
        arg_outfile.write(f"isolate_pairs: {args.isolate_pairs}\n")
        arg_outfile.write(f"output_folder: {args.output_folder}\n")

    find_overlap_write_outputfiles(
        event_outpath,
        status_outpath,
        isolate_DOC_dict,
        isolate_patient_mapping_dict,
        patient_address_dict,
        isolate_pairs_donorkey_dict,
        isolate_pairs_recipientkey_dict,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())