"""
Procedure_epiOverlap.py.

Description:
    Script for computing procedure epidemiological overlap based on patient admission data.

Author:
    Peng Ken Lim
    &
    MAI-Code-1.1-Flash

Date updated:
    2026-09-16

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

        --patient_admission_details:
            Patient_ID: Column 1
            Age: Column 2
            Gender: Column 3
            Admission Date: Column 4
            Discharge Date: Column 5
            Admission Hospital: Column 6
            Ward: Column 7
            Bed: Column 8
            Discipline: Column 9
            Start Date: Column 10
            Stop Date: Column 11

            Example rows:
                PID101    45    M    2020-01-01    2020-01-10    Hospital A    Ward 1    Bed 5    Cardiology    2020-01-01    2020-01-05
                PID102    60    F    2020-02-01    2020-02-15    Hospital B    Ward 2    Bed 10    Neurology    2020-02-01    2020-02-10

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
        python ./tools/Procedure_epiOverlap.py [options]
        options:
            --isolate_DOC                 Path to the isolate Date-of-culture TSV. Expected column order: 1,2 --> Isolate_ID, Date of Culture (DOC)
            --isolate_patient_mapping     Path to the isolate-to-patient mapping TSV. Expected column order: 1,2 --> Isolate_ID, Patient_ID.
            --patient_procedure_details   Path to the patient procedure details TSV. Expected column order: 1,2,3,4,5,6,7,8,9,10,11 --> Patient_ID, Age, Gender, Admission Date, Discharge Date, Admission Hospital, Ward, Bed, Discipline, Start Date, Stop Date.
            --isolate_pairs               Path to the isolate pair TSV. Expected column order: 1,2 --> Recip_isolate_ID, Donor_isolate_ID.
            --output_folder               Path to the output directory for generated TSV files.
            --help                        Show this help message and exit.

        additional information:
            You can override the default column order of all input files by specifying the columns explicitly in their corresponding argument flags
            for e.g,
                ---patient_procedure_details /path/to/file.tsv[1,2,3,4,5,6,7,8,9,10,11]
                implies the following:
                Placeholder
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


class ParsedDate(date):
    """A date subclass that preserves the original decimal-year input string when present."""

    __slots__ = ("_decimal_value",)

    def __new__(cls, value: date, decimal_value: str | None = None):
        self = super().__new__(cls, value.year, value.month, value.day)
        self._decimal_value = decimal_value
        return self

    @property
    def decimal_value(self):
        return self._decimal_value


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


def _stringify_date_value(value, decimal_output: bool = False):
    """Render parsed dates as ISO values or decimal-year values while leaving empty values blank."""
    if value is None:
        return ""
    if isinstance(value, ParsedDate) and decimal_output and value.decimal_value is not None:
        return str(value.decimal_value)
    if isinstance(value, date):
        if decimal_output:
            year_start = date(value.year, 1, 1)
            day_of_year = (value - year_start).days + 1
            days_in_year = 366 if ((value.year % 4 == 0 and value.year % 100 != 0) or (value.year % 400 == 0)) else 365
            decimal = value.year + (day_of_year - 1) / days_in_year
            return f"{decimal:.6f}"
        return value.isoformat()
    if value in {"", "n.a", "na", "nan", "null"}:
        return ""
    return str(value)


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

    try:
        decimal_year = float(date_str)
        if "." in date_str and not date_str.startswith(("+", "-")):
            year = int(decimal_year)
            fraction = decimal_year - year
            leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
            days_in_year = 366 if leap_year else 365
            day_of_year = int(round(fraction * days_in_year))
            day_of_year = max(1, min(day_of_year, days_in_year))
            parsed_date = date(year, 1, 1) + timedelta(days=day_of_year - 1)
            return ParsedDate(parsed_date, date_str)
    except ValueError:
        pass

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

    return None


def build_parser() -> argparse.ArgumentParser:
    """
    Construct the CLI argument parser for the discipline overlap workflow.

    Returns:
        argparse.ArgumentParser: Configured parser for the workflow CLI.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Compute epidemiological overlap of isolate transmission based on "
            "patient procedure data.\n\n"
            "Expected column order (not exact header-name matching):\n"
            "  --isolate_DOC: Isolate_ID, Date of Culture (DOC)\n"
            "  --isolate_patient_mapping: Isolate_ID, Patient_ID\n"
            "  --patient_procedure_details: Patient_ID, Procedure Hospital, Procedure Type 1, Procedure Type 2, ...\n"
            "  --isolate_pairs: Recip_isolate_ID, Donor_isolate_ID\n\n"
            "The procedure details file does not support explicit column-order overrides."
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
        "--patient_procedure_details",
        "--patient_admission_details",
        dest="patient_procedure_details",
        type=str,
        required=True,
        help=(
            "Path to the patient procedure-details TSV. "
            "Expected column order: Patient_ID, Procedure Hospital, Procedure Type columns, each with a date value. "
            "This tool does not support column-order overrides."
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
        "--decimal_date",
        action="store_true",
        help=(
            "Write date outputs in decimal-year format instead of ISO YYYY-MM-DD. "
            "Default: YYYY-MM-DD."
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


def parse_patient_procedure_details(file_path: str):
    """
    Parse the patient procedure details input file.

    Supported inputs include decimal-year values such as ``2010.682192`` as
    well as common calendar formats such as ISO dates, slash dates, and text
    dates. When slash dates are present, the format is inferred from the whole
    column before parsing to reduce ambiguity.

    Returns:
        dict[str, list[dict[str, object]]]: Mapping from patient ID to a list
        of procedure entries containing the procedure hospital and parsed date
        values for each procedure type.
    """
    patient_procedure_dict = {}
    rows = []

    with open(file_path, "r", encoding="utf-8") as infile:
        for line in infile:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(stripped.split("\t"))

    if not rows:
        return [], patient_procedure_dict

    procedure_types = rows[0][2:]
    date_format_by_column = {}

    for column_index in range(len(procedure_types)):
        column_values = []
        for row in rows[1:]:
            if len(row) <= 2 + column_index:
                continue
            raw_value = row[2 + column_index].strip()
            for value in raw_value.split(","):
                value = value.strip()
                if value.lower() in {"", "n.a", "na", "nan", "null"}:
                    continue
                column_values.append(value)

        if not column_values:
            continue

        slash_format = infer_slash_date_format(column_values)
        hyphen_format = infer_hyphen_date_format(column_values)
        date_format_by_column[column_index] = (slash_format, hyphen_format)

    for row in rows[1:]:
        if len(row) < 2:
            continue

        patient_id = row[0].strip()
        procedure_hospital = row[1].strip()
        if patient_id not in patient_procedure_dict:
            patient_procedure_dict[patient_id] = []

        for procedure_index, procedure_type in enumerate(procedure_types):
            if len(row) <= 2 + procedure_index:
                continue

            raw_value = row[2 + procedure_index].strip()
            procedure_dates = [item.strip() for item in raw_value.split(",") if item.strip()]
            if not procedure_dates:
                continue

            for procedure_date in procedure_dates:
                if procedure_date.lower() in {"", "n.a", "na", "nan", "null"}:
                    continue

                slash_format, hyphen_format = date_format_by_column.get(
                    procedure_index,
                    (None, None),
                )
                parsed_date = parse_date_string(
                    procedure_date,
                    slash_format=slash_format,
                    hyphen_format=hyphen_format,
                )
                if parsed_date is None:
                    raise ValueError(
                        f"Could not parse date for patient '{patient_id}' and procedure '{procedure_type}': {procedure_date!r}"
                    )

                patient_procedure_dict[patient_id].append({
                    "Procedure Hospital": procedure_hospital,
                    "Procedure Type": procedure_type,
                    "Procedure Date": parsed_date,
                })

    return procedure_types, patient_procedure_dict


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
                            procedure_types,
                            patient_procedure_dict,
                             isolate_pairs_donorkey_dict,
                             isolate_pairs_recipientkey_dict,
                             decimal_output: bool = False):
    """

    """
    def format_output_value(value):
        return _stringify_date_value(value, decimal_output)

    event_outfile_line_contents = ["\t".join([
        "Overlap_event_type",
        "Recip_patient_ID", "Recip_isolate_ID",
        "Recip_isolate_DOC",
        "Recip_procedure_hospital",
        "Recip_procedure",
        "Recip_procedure_date",
        "Donor_patient_ID", "Donor_isolate_ID",
        "Donor_isolate_DOC",
        "Donor_procedure_hospital",
        "Donor_procedure",
        "Donor_procedure_date"
    ])]
    status_outfile_line_contents = ["\t".join([
        "Recip_isolate_ID", "Donor_isolate_ID", "Recip_patient_ID", "Donor_patient_ID",
        "Direct_procedure_contact", #procedure-hospital match on the same day
        "Indirect_procedure_contact", #procedure-hospital match. Not on the same day but donor procedure precedes recipient procedure
        "No_procedure_contact", # No procedure-hospital match or recpipient procedure proceeds donor     
        "Date_OOR", # procedure date out of risk period
        "No_procedure" # No procedure recorded for either donor or recipient
    ])]

    for donor_isolate_id, recipient_isolate_ids in isolate_pairs_donorkey_dict.items():
        donor_patient_id = isolate_patient_mapping_dict.get(donor_isolate_id)
        donor_procedure_details_list = patient_procedure_dict.get(donor_patient_id, [])
        donor_isolate_DOC = isolate_DOC_dict.get(donor_isolate_id)

        for recipient_isolate_id in recipient_isolate_ids:
            recipient_patient_id = isolate_patient_mapping_dict.get(recipient_isolate_id)
            recipient_procedure_details_list = patient_procedure_dict.get(recipient_patient_id, [])
            recipient_isolate_DOC = isolate_DOC_dict.get(recipient_isolate_id)

            procedure_contact_direct = False
            procedure_contact_indirect = False
            procedure_no_contact = False
            date_oor = False
            procedure_no_procedure = False

            if not donor_procedure_details_list or not recipient_procedure_details_list:
                procedure_no_procedure = True
            else:
                for donor_procedure_details in donor_procedure_details_list:
                    donor_procedure_date = parse_date_string(donor_procedure_details.get("Procedure Date"))
                    donor_procedure_type = donor_procedure_details.get("Procedure Type")
                    donor_procedure_hospital = donor_procedure_details.get("Procedure Hospital")

                    if donor_procedure_date is None:
                        continue

                    if donor_procedure_date < donor_isolate_DOC or donor_procedure_date > recipient_isolate_DOC:
                        date_oor = True
                        continue

                    for recipient_procedure_details in recipient_procedure_details_list:
                        recipient_procedure_date = parse_date_string(recipient_procedure_details.get("Procedure Date"))
                        recipient_procedure_type = recipient_procedure_details.get("Procedure Type")
                        recipient_procedure_hospital = recipient_procedure_details.get("Procedure Hospital")

                        if recipient_procedure_date is None:
                            continue

                        if recipient_procedure_date < donor_isolate_DOC or recipient_procedure_date > recipient_isolate_DOC:
                            date_oor = True
                            continue

                        if (
                            donor_procedure_type != recipient_procedure_type
                            or donor_procedure_hospital != recipient_procedure_hospital
                        ):
                            procedure_no_contact = True
                            event_outfile_line_contents.append("\t".join([
                                "No Procedure Contact",
                                format_output_value(recipient_patient_id),
                                format_output_value(recipient_isolate_id),
                                format_output_value(recipient_isolate_DOC),
                                format_output_value(recipient_procedure_hospital),
                                format_output_value(recipient_procedure_type),
                                format_output_value(recipient_procedure_date),
                                format_output_value(donor_patient_id),
                                format_output_value(donor_isolate_id),
                                format_output_value(donor_isolate_DOC),
                                format_output_value(donor_procedure_hospital),
                                format_output_value(donor_procedure_type),
                                format_output_value(donor_procedure_date),
                            ]))
                            continue

                        if donor_procedure_date > recipient_procedure_date:
                            procedure_no_contact = True
                            event_outfile_line_contents.append("\t".join([
                                "No Procedure Contact",
                                format_output_value(recipient_patient_id),
                                format_output_value(recipient_isolate_id),
                                format_output_value(recipient_isolate_DOC),
                                format_output_value(recipient_procedure_hospital),
                                format_output_value(recipient_procedure_type),
                                format_output_value(recipient_procedure_date),
                                format_output_value(donor_patient_id),
                                format_output_value(donor_isolate_id),
                                format_output_value(donor_isolate_DOC),
                                format_output_value(donor_procedure_hospital),
                                format_output_value(donor_procedure_type),
                                format_output_value(donor_procedure_date),
                            ]))
                        elif donor_procedure_date == recipient_procedure_date:
                            procedure_contact_direct = True
                            event_outfile_line_contents.append("\t".join([
                                "Procedure Direct",
                                format_output_value(recipient_patient_id),
                                format_output_value(recipient_isolate_id),
                                format_output_value(recipient_isolate_DOC),
                                format_output_value(recipient_procedure_hospital),
                                format_output_value(recipient_procedure_type),
                                format_output_value(recipient_procedure_date),
                                format_output_value(donor_patient_id),
                                format_output_value(donor_isolate_id),
                                format_output_value(donor_isolate_DOC),
                                format_output_value(donor_procedure_hospital),
                                format_output_value(donor_procedure_type),
                                format_output_value(donor_procedure_date)
                            ]))
                        else:
                            procedure_contact_indirect = True
                            event_outfile_line_contents.append("\t".join([
                                "Procedure Indirect",
                                format_output_value(recipient_patient_id),
                                format_output_value(recipient_isolate_id),
                                format_output_value(recipient_isolate_DOC),
                                format_output_value(recipient_procedure_hospital),
                                format_output_value(recipient_procedure_type),
                                format_output_value(recipient_procedure_date),
                                format_output_value(donor_patient_id),
                                format_output_value(donor_isolate_id),
                                format_output_value(donor_isolate_DOC),
                                format_output_value(donor_procedure_hospital),
                                format_output_value(donor_procedure_type),
                                format_output_value(donor_procedure_date),
                            ]))

            status_outfile_line_contents.append("\t".join([
                format_output_value(recipient_isolate_id),
                format_output_value(donor_isolate_id),
                format_output_value(recipient_patient_id),
                format_output_value(donor_patient_id),
                "Procedure Direct" if procedure_contact_direct else "",
                "Procedure Indirect" if procedure_contact_indirect else "",
                "No Procedure Contact" if procedure_no_contact else "",
                "Date_OOR" if date_oor else "",
                "No Procedure for patient" if procedure_no_procedure else ""
            ]))

    with open(event_outpath, "w", encoding="utf-8") as event_handle:
        event_handle.write("\n".join(event_outfile_line_contents) + "\n")

    with open(status_outpath, "w", encoding="utf-8") as status_handle:
        status_handle.write("\n".join(status_outfile_line_contents) + "\n")


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
    print(f"  patient_procedure_details: {args.patient_procedure_details}")
    print(f"  isolate_pairs: {args.isolate_pairs}")
    print(f"  output_folder: {args.output_folder}")

    # Parse the input files
    isolate_DOC_dict = parse_isolate_DOC(args.isolate_DOC)
    isolate_patient_mapping_dict, _ = parse_isolate_patient_mapping(args.isolate_patient_mapping)
    procedure_types, patient_procedure_dict = parse_patient_procedure_details(args.patient_procedure_details)
    isolate_pairs_donorkey_dict, isolate_pairs_recipientkey_dict = parse_isolate_pairs(args.isolate_pairs)

    os.makedirs(args.output_folder, exist_ok=True)
    event_outpath = os.path.join(args.output_folder, "Procedure_epiOverlap_events.tsv")
    status_outpath = os.path.join(args.output_folder, "Procedure_epiOverlap_statuses_all_pairs.tsv")

    with open(os.path.join(args.output_folder, "Procedure_epiOverlap_Argslog.txt"), "w", encoding="utf-8") as arg_outfile:
        arg_outfile.write(f"isolate_DOC: {args.isolate_DOC}\n")
        arg_outfile.write(f"isolate_patient_mapping: {args.isolate_patient_mapping}\n")
        arg_outfile.write(f"patient_procedure_details: {args.patient_procedure_details}\n")
        arg_outfile.write(f"isolate_pairs: {args.isolate_pairs}\n")
        arg_outfile.write(f"decimal_date: {args.decimal_date}\n")
        arg_outfile.write(f"output_folder: {args.output_folder}\n")

    find_overlap_write_outputfiles(
        event_outpath,
        status_outpath,
        isolate_DOC_dict,
        isolate_patient_mapping_dict,
        procedure_types,
        patient_procedure_dict,
        isolate_pairs_donorkey_dict,
        isolate_pairs_recipientkey_dict,
        decimal_output=args.decimal_date,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
