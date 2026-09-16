"""
Adm_epiOverlap.py.

Description:
    script for computing hospital, ward and bed epidemiological overlap based on patient admission data.

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
        python ./tools/Adm_epiOverlap.py [options]
        options:
            --isolate_DOC                 Path to the isolate Date-of-culture TSV. Expected column order: 1,2 --> Isolate_ID, Date of Culture (DOC)
            --isolate_patient_mapping     Path to the isolate-to-patient mapping TSV. Expected column order: 1,2 --> Isolate_ID, Patient_ID.
            --patient_admission_details   Path to the patient admission details TSV. Expected column order: 1,2,3,4,5,6,7,8,9,10,11 --> Patient_ID, Age, Gender, Admission Date, Discharge Date, Admission Hospital, Ward, Bed, Discipline, Start Date, Stop Date.
            --isolate_pairs               Path to the isolate pair TSV. Expected column order: 1,2 --> Recip_isolate_ID, Donor_isolate_ID.
            --decimal_date                Write date outputs in decimal-year format instead of ISO YYYY-MM-DD.
            --output_folder               Path to the output directory for generated TSV files.
            --help                        Show this help message and exit.

        additional information:
            You can override the default column order of all input files by specifying the columns explicitly in their corresponding argument flags
            for e.g,
                ---patient_admission_details /path/to/file.tsv[1,2,3,4,5,6,7,8,9,10,11]
                implies the following:
                    Column 1 in the file corresponds to Patient_ID
                    Column 2 in the file corresponds to Age
                    Column 3 in the file corresponds to Gender
                    Column 4 in the file corresponds to Admission Date
                    Column 5 in the file corresponds to Discharge Date
                    Column 6 in the file corresponds to Admission Hospital
                    Column 7 in the file corresponds to Ward
                    Column 8 in the file corresponds to Bed
                    Column 9 in the file corresponds to Discipline
                    Column 10 in the file corresponds to Start Date
                    Column 11 in the file corresponds to Stop Date
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
        if not date_str.startswith(("+", "-")):
            year = int(decimal_year)
            if "." not in date_str or decimal_year == float(year):
                return ParsedDate(date(year, 1, 1), date_str)
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
    Construct the CLI argument parser for the hospital, ward, and bed overlap workflow.

    Returns:
        argparse.ArgumentParser: Configured parser for the workflow CLI.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Compute hospital, ward, and bed epidemiological overlap of isolate transmission "
            "based on patient admission data.\n\n"
            "Expected column order (not exact header-name matching):\n"
            "  --isolate_DOC: Isolate_ID, Date of Culture (DOC)\n"
            "  --isolate_patient_mapping: Isolate_ID, Patient_ID\n"
            "  --patient_admission_details: Patient_ID, Age, Gender, Admission Date, "
            "Discharge Date, Admission Hospital, Ward, Bed, Discipline, Start Date, Stop Date\n"
            "  --isolate_pairs: Recip_isolate_ID, Donor_isolate_ID\n\n"
            "Override column positions per file with syntax like:\n"
            "  --patient_admission_details /path/to/file.tsv[1,2,3,4,5,6,7,8,9,10,11]"
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
        "--patient_admission_details",
        dest="patient_admission_details",
        type=str,
        required=True,
        help=(
            "Path to the patient admission-details TSV. "
            "Expected column order: Patient_ID, Age, Gender, Admission Date, Discharge Date, "
            "Admission Hospital, Ward, Bed, Discipline, Start Date, Stop Date. "
            "Optional override: /path/to/file.tsv[1,2,3,4,5,6,7,8,9,10,11]."
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


def parse_patient_adm_details(file_path: str):
    """
    Parse the patient admission-details input file.

    Each row is expected to contain:
        Patient_ID, Age, Gender, Admission Date, Discharge Date,
        Admission Hospital, Ward, Bed, Discipline, Start Date, Stop Date

    Date columns are parsed using the same format-agnostic logic as the DOC file,
    with the format inferred separately for each date column and assumed to be
    consistent within that column.

    Returns:
        dict[str, list[dict[str, str]]]: A mapping from patient ID to a list of
        admission records, each stored as a dictionary of field names to values.
    """
    patient_admission_dict = {}
    rows = _read_tsv_rows(file_path, expected_columns=11)

    date_columns = {
        "Admission Date": 3,
        "Discharge Date": 4,
        "Start Date": 9,
        "Stop Date": 10,
    }
    date_values = {name: [] for name in date_columns}
    for line_idx, row in enumerate(rows):
        if line_idx == 0:
            continue
        for column_name, column_index in date_columns.items():
            value = row[column_index].strip() if column_index < len(row) else ""
            if value.lower() not in {"", "n.a", "na", "nan", "null"}:
                date_values[column_name].append(value)

    date_formats = {
        column_name: {
            "slash": infer_slash_date_format(values),
            "hyphen": infer_hyphen_date_format(values),
        }
        for column_name, values in date_values.items()
    }

    for line_idx, row in enumerate(rows):
        if line_idx == 0:
            continue
        (
            patient_id,
            age,
            gender,
            admission_date,
            discharge_date,
            admission_hospital,
            ward,
            bed,
            discipline,
            start_date,
            stop_date,
        ) = row[:11]

        parsed_dates = {}
        for column_name, value in {
            "Admission Date": admission_date,
            "Discharge Date": discharge_date,
            "Start Date": start_date,
            "Stop Date": stop_date,
        }.items():
            value = value.strip()
            if value.lower() in {"", "n.a", "na", "nan", "null"}:
                parsed_dates[column_name] = None
                continue

            slash_format = date_formats[column_name]["slash"]
            hyphen_format = date_formats[column_name]["hyphen"]
            parsed_value = parse_date_string(value, slash_format=slash_format, hyphen_format=hyphen_format)
            if parsed_value is None:
                raise ValueError(f"Could not parse date for patient '{patient_id}' in {column_name}: {value!r}")
            parsed_dates[column_name] = parsed_value

        record = {
            "Patient_ID": patient_id,
            "Age": age,
            "Gender": gender,
            "Admission Date": parsed_dates["Admission Date"],
            "Discharge Date": parsed_dates["Discharge Date"],
            "Admission Hospital": admission_hospital,
            "Ward": ward,
            "Bed": bed,
            "Discipline": discipline,
            "Start Date": parsed_dates["Start Date"],
            "Stop Date": parsed_dates["Stop Date"],
        }
        if patient_id not in patient_admission_dict:
            patient_admission_dict[patient_id] = []
        patient_admission_dict[patient_id].append(record)
    return patient_admission_dict


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


def clip_recipient_interval(start, stop, donor_doc, recip_doc):
    """
    Match the Perl logic for recipient admissions.
    Returns (clipped_start, clipped_stop) or None if outside the risk window.
    """
    if start in (None, "n.a") or stop in (None, "n.a"):
        return None

    clipped_start = None
    clipped_stop = None

    # RECIP_START
    if start <= recip_doc:
        if start >= donor_doc:
            clipped_start = start
        else:
            if stop >= donor_doc:
                clipped_start = donor_doc

    # RECIP_STOP
    if stop <= recip_doc:
        if stop >= donor_doc:
            clipped_stop = stop
    else:
        if start <= recip_doc:
            clipped_stop = recip_doc

    if clipped_start is None:
        return None

    return clipped_start, clipped_stop


def clip_donor_interval(start, stop, donor_doc, recip_doc):
    """
    Match the Perl logic for donor admissions.
    Returns (clipped_start, clipped_stop) or None if outside the risk window.
    """
    if start in (None, "n.a") or stop in (None, "n.a"):
        return None

    clipped_start = None
    clipped_stop = None

    # DONOR_START
    if start >= donor_doc:
        if start > recip_doc:
            # donor start is after recipient DOC; effectively out of range
            pass
        else:
            clipped_start = start
    else:
        if stop >= donor_doc:
            clipped_start = donor_doc

    # DONOR_STOP
    if stop >= donor_doc:
        if stop > recip_doc:
            if start <= recip_doc:
                clipped_stop = recip_doc
        else:
            clipped_stop = stop

    if clipped_start is None:
        return None

    return clipped_start, clipped_stop


def find_overlap_write_outputfiles(event_outpath, status_outpath,
                             isolate_DOC_dict,
                             isolate_patient_mapping_dict,
                            patient_admission_dict,
                             isolate_pairs_donorkey_dict,
                             isolate_pairs_recipientkey_dict,
                             decimal_output: bool = False):
    """
    Detect hospital, ward, and bed overlaps and write the event and status TSV outputs.

    The function compares recipient-donor isolate pairs, resolves each isolate to
    its patient and admission details, and writes a tab-delimited event log plus a summary
    status table describing whether hospital, ward, and bed overlaps occurred.

    Args:
        event_outpath: Output path for the overlap event TSV.
        status_outpath: Output path for the pair-level status TSV.
        isolate_DOC_dict: Mapping of isolate IDs to culture dates.
        isolate_patient_mapping_dict: Mapping of isolate IDs to patient IDs.
        patient_admission_dict: Mapping of patient IDs to admission details.
        isolate_pairs_donorkey_dict: Mapping of donor isolate IDs to recipient isolate IDs.
        isolate_pairs_recipientkey_dict: Mapping of recipient isolate IDs to donor isolate IDs.
        decimal_output: If True, writes date values in decimal-year format.

    Returns:
        None. Output files are written to disk.
    """
    def format_output_value(value):
        return _stringify_date_value(value, decimal_output)

    event_outfile_line_contents = ["\t".join([
        "Hospital_Overlap_event_type",
        "Ward_Overlap_event_type",
        "Bed_Overlap_event_type",
        "Recip_patient_ID", "Recip_isolate_ID",
        "Recip_isolate_DOC",
        "Recip_Age", "Recip_Gender", "Recip_Admission_date", "Recip_Discharge_Date",
        "Recip_Admission_Hospital", "Recip_Ward", "Recip_Bed",
        "Recip_Discipline", "Recip_start_date", "Recip_end_date",
        "Donor_patient_ID", "Donor_isolate_ID",
        "Donor_isolate_DOC",
        "Donor_Age", "Donor_Gender", "Donor_Admission_date", "Donor_Discharge_Date",
        "Donor_Admission_Hospital", "Donor_Ward", "Donor_Bed",
        "Donor_Discipline", "Donor_start_date", "Donor_end_date"
    ])]
    status_outfile_line_contents = ["\t".join([
        "Recip_isolate_ID", "Donor_isolate_ID", "Recip_patient_ID", "Donor_patient_ID",
        "Direct_exact_hospital_contact",
        "Direct_partial_hospital_contact",
        "Indirect_hospital_contact",
        "No_hospital_contact",
        "Direct_exact_ward_contact",
        "Direct_partial_ward_contact",
        "Indirect_ward_contact",
        "No_ward_contact",
        "Indirect_bed_contact",
        "No_bed_contact",
        "Date_OOR"
    ])]

    for donor_isolate_id, recipient_isolate_ids in isolate_pairs_donorkey_dict.items():
        donor_patient_id = isolate_patient_mapping_dict.get(donor_isolate_id)
        donor_admission_details = patient_admission_dict.get(donor_patient_id, [])
        donor_isolate_DOC = isolate_DOC_dict.get(donor_isolate_id)

        for recipient_isolate_id in recipient_isolate_ids:
            recipient_patient_id = isolate_patient_mapping_dict.get(recipient_isolate_id)
            recipient_admission_details = patient_admission_dict.get(recipient_patient_id, [])
            recipient_isolate_DOC = isolate_DOC_dict.get(recipient_isolate_id)

            pair_Direct_exact_hospital_contact = False
            pair_Direct_partial_hospital_contact = False
            pair_Indirect_hospital_contact = False
            pair_No_hospital_contact = False
            pair_Direct_exact_ward_contact = False
            pair_Direct_partial_ward_contact = False
            pair_Indirect_ward_contact = False
            pair_No_ward_contact = False
            pair_Indirect_bed_contact = False
            pair_No_bed_contact = False
            Date_OOR = False

            for donor_stay_admission_details in donor_admission_details:
                donor_stay_start = parse_date_string(donor_stay_admission_details.get("Start Date"))
                donor_stay_end = parse_date_string(donor_stay_admission_details.get("Stop Date"))
                donor_clipped = clip_donor_interval(donor_stay_start, donor_stay_end, donor_isolate_DOC, recipient_isolate_DOC)
                if donor_clipped is None:
                    Date_OOR = True
                    continue

                donor_stay_start_clipped, donor_stay_stop_clipped = donor_clipped

                for recipient_stay_admission_details in recipient_admission_details:
                    recipient_stay_start = parse_date_string(recipient_stay_admission_details.get("Start Date"))
                    recipient_stay_end = parse_date_string(recipient_stay_admission_details.get("Stop Date"))
                    recipient_clipped = clip_recipient_interval(recipient_stay_start, recipient_stay_end, donor_isolate_DOC, recipient_isolate_DOC)
                    if recipient_clipped is None:
                        Date_OOR = True
                        continue

                    recipient_stay_start_clipped, recipient_stay_stop_clipped = recipient_clipped

                    Hospital_Overlap_event_type = "No Hospital Contact"
                    Ward_Overlap_event_type = "No Ward Contact"
                    Bed_Overlap_event_type = "No Bed Contact"

                    if recipient_stay_admission_details.get("Admission Hospital") == donor_stay_admission_details.get("Admission Hospital"):
                        if donor_stay_start_clipped == recipient_stay_start_clipped and donor_stay_stop_clipped == recipient_stay_stop_clipped:
                            pair_Direct_exact_hospital_contact = True
                            Hospital_Overlap_event_type = "Hospital Direct (Exact)"
                            if recipient_stay_admission_details.get("Ward") == donor_stay_admission_details.get("Ward"):
                                pair_Direct_exact_ward_contact = True
                                Ward_Overlap_event_type = "Ward Direct (Exact)"
                            else:
                                pair_No_ward_contact = True
                                Ward_Overlap_event_type = "No Ward Contact"
                            pair_No_bed_contact = True
                            Bed_Overlap_event_type = "No Bed Contact"
                        elif donor_stay_start_clipped <= recipient_stay_stop_clipped and donor_stay_stop_clipped >= recipient_stay_start_clipped:
                            pair_Direct_partial_hospital_contact = True
                            Hospital_Overlap_event_type = "Hospital Direct"
                            if recipient_stay_admission_details.get("Ward") == donor_stay_admission_details.get("Ward"):
                                pair_Direct_partial_ward_contact = True
                                Ward_Overlap_event_type = "Ward Direct"
                            else:
                                pair_No_ward_contact = True
                                Ward_Overlap_event_type = "No Ward Contact"
                            pair_No_bed_contact = True
                            Bed_Overlap_event_type = "No Bed Contact"
                        elif donor_stay_stop_clipped < recipient_stay_start_clipped: 
                            pair_Indirect_hospital_contact = True
                            Hospital_Overlap_event_type = "Hospital Indirect"
                            if recipient_stay_admission_details.get("Ward") == donor_stay_admission_details.get("Ward"):
                                pair_Indirect_ward_contact = True
                                Ward_Overlap_event_type = "Ward Indirect"
                                if recipient_stay_admission_details.get("Bed") == donor_stay_admission_details.get("Bed"):
                                    pair_Indirect_bed_contact = True
                                    Bed_Overlap_event_type = "Bed Indirect"
                                else:
                                    pair_No_bed_contact = True
                                    Bed_Overlap_event_type = "No Bed Contact"
                            else:
                                pair_No_ward_contact = True
                                Ward_Overlap_event_type = "No Ward Contact"
                                pair_No_bed_contact = True
                                Bed_Overlap_event_type = "No Bed Contact"
                        else: # no temporal overlap AND recipient stay is before donor stay
                            pair_No_hospital_contact = True
                            Hospital_Overlap_event_type = "No Hospital Contact"
                            pair_No_ward_contact = True
                            Ward_Overlap_event_type = "No Ward Contact"
                            pair_No_bed_contact = True
                            Bed_Overlap_event_type = "No Bed Contact"
                    else: # hospital not the same
                        pair_No_hospital_contact = True
                        Hospital_Overlap_event_type = "No Hospital Contact"
                        pair_No_ward_contact = True
                        Ward_Overlap_event_type = "No Ward Contact"
                        pair_No_bed_contact = True
                        Bed_Overlap_event_type = "No Bed Contact"

                    event_outfile_line_contents.append("\t".join([
                        Hospital_Overlap_event_type,
                        Ward_Overlap_event_type,
                        Bed_Overlap_event_type,
                        format_output_value(recipient_patient_id),
                        format_output_value(recipient_isolate_id),
                        format_output_value(recipient_isolate_DOC),
                        format_output_value(recipient_stay_admission_details.get("Age", "")),
                        format_output_value(recipient_stay_admission_details.get("Gender", "")),
                        format_output_value(recipient_stay_admission_details.get("Admission Date", "")),
                        format_output_value(recipient_stay_admission_details.get("Discharge Date", "")),
                        format_output_value(recipient_stay_admission_details.get("Admission Hospital", "")),
                        format_output_value(recipient_stay_admission_details.get("Ward", "")),
                        format_output_value(recipient_stay_admission_details.get("Bed", "")),
                        format_output_value(recipient_stay_admission_details.get("Discipline", "")),
                        format_output_value(recipient_stay_admission_details.get("Start Date", "")),
                        format_output_value(recipient_stay_admission_details.get("Stop Date", "")),
                        format_output_value(donor_patient_id),
                        format_output_value(donor_isolate_id),
                        format_output_value(donor_isolate_DOC),
                        format_output_value(donor_stay_admission_details.get("Age", "")),
                        format_output_value(donor_stay_admission_details.get("Gender", "")),
                        format_output_value(donor_stay_admission_details.get("Admission Date", "")),
                        format_output_value(donor_stay_admission_details.get("Discharge Date", "")),
                        format_output_value(donor_stay_admission_details.get("Admission Hospital", "")),
                        format_output_value(donor_stay_admission_details.get("Ward", "")),
                        format_output_value(donor_stay_admission_details.get("Bed", "")),
                        format_output_value(donor_stay_admission_details.get("Discipline", "")),
                        format_output_value(donor_stay_admission_details.get("Start Date", "")),
                        format_output_value(donor_stay_admission_details.get("Stop Date", "")),
                    ]))

            status_outfile_line_contents.append("\t".join([
                format_output_value(recipient_isolate_id),
                format_output_value(donor_isolate_id),
                format_output_value(recipient_patient_id),
                format_output_value(donor_patient_id),
                "Hospital Direct (Exact)" if pair_Direct_exact_hospital_contact else "",
                "Hospital Direct" if pair_Direct_partial_hospital_contact else "",
                "Hospital Indirect" if pair_Indirect_hospital_contact else "",
                "No Hospital Contact" if pair_No_hospital_contact else "",
                "Ward Direct (Exact)" if pair_Direct_exact_ward_contact else "",
                "Ward Direct" if pair_Direct_partial_ward_contact else "",
                "Ward Indirect" if pair_Indirect_ward_contact else "",
                "No Ward Contact" if pair_No_ward_contact else "",
                "Bed Indirect" if pair_Indirect_bed_contact else "",
                "No Bed Contact" if pair_No_bed_contact else "",
                "Date_OOR" if Date_OOR else "",
            ]))

    with open(event_outpath, "w", encoding="utf-8") as event_handle:
        event_handle.write("\n".join(event_outfile_line_contents) + "\n")

    with open(status_outpath, "w", encoding="utf-8") as status_handle:
        status_handle.write("\n".join(status_outfile_line_contents) + "\n")


def main() -> int:
    """
    Execute the epidemiological overlap workflow from the command line.

    This function parses the required arguments, loads the input TSV files,
    computes hospital, ward, and bed overlaps between pairs of isolates, and writes the
    output files to the requested folder.

    Returns:
        int: Exit code for the CLI command. Returns 0 on successful execution.
    """
    parser = build_parser()
    args = parser.parse_args()

    print("Input arguments:")
    print(f"  isolate_DOC: {args.isolate_DOC}")
    print(f"  isolate_patient_mapping: {args.isolate_patient_mapping}")
    print(f"  patient_admission_details: {args.patient_admission_details}")
    print(f"  isolate_pairs: {args.isolate_pairs}")
    print(f"  output_folder: {args.output_folder}")

    # Parse the input files
    isolate_DOC_dict = parse_isolate_DOC(args.isolate_DOC)
    isolate_patient_mapping_dict, _ = parse_isolate_patient_mapping(args.isolate_patient_mapping)
    patient_admission_dict = parse_patient_adm_details(args.patient_admission_details)
    isolate_pairs_donorkey_dict, isolate_pairs_recipientkey_dict = parse_isolate_pairs(args.isolate_pairs)

    os.makedirs(args.output_folder, exist_ok=True)
    event_outpath = os.path.join(args.output_folder, "Adm_epiOverlap_events.tsv")
    status_outpath = os.path.join(args.output_folder, "Adm_epiOverlap_statuses_all_pairs.tsv")

    with open(os.path.join(args.output_folder, "Adm_epiOverlap_Argslog.txt"), "w", encoding="utf-8") as arg_outfile:
        arg_outfile.write(f"isolate_DOC: {args.isolate_DOC}\n")
        arg_outfile.write(f"isolate_patient_mapping: {args.isolate_patient_mapping}\n")
        arg_outfile.write(f"patient_admission_details: {args.patient_admission_details}\n")
        arg_outfile.write(f"isolate_pairs: {args.isolate_pairs}\n")
        arg_outfile.write(f"decimal_date: {args.decimal_date}\n")
        arg_outfile.write(f"output_folder: {args.output_folder}\n")

    find_overlap_write_outputfiles(
        event_outpath,
        status_outpath,
        isolate_DOC_dict,
        isolate_patient_mapping_dict,
        patient_admission_dict,
        isolate_pairs_donorkey_dict,
        isolate_pairs_recipientkey_dict,
        decimal_output=args.decimal_date,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
