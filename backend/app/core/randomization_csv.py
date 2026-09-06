"""
Parse a pre-randomized sequence CSV and return validated rows.

Expected columns (case-insensitive, leading/trailing whitespace stripped):
    sequence_number  – positive integer, unique within the file
    kit_code         – non-empty string, globally unique
    short_code       – treatment arm short code (must match a study arm)
    treatment_arm    – treatment arm name (informational; stored as-is)

The `treatment_arm` column is optional.  If absent, `treatment_name` is set to
the short_code value so something human-readable is still stored.
"""

from __future__ import annotations

import csv
import io
from typing import TypedDict


REQUIRED_COLUMNS = {"sequence_number", "kit_code", "short_code"}


class ParsedRow(TypedDict):
    sequence_number: int
    kit_code: str
    short_code: str
    treatment_name: str


def parse_randomization_csv(content: bytes) -> list[ParsedRow]:
    """
    Parse *content* (raw bytes of a CSV file) and return a list of ParsedRow
    dicts.  Raises ``ValueError`` with a human-readable message on any problem.
    """
    try:
        text = content.decode("utf-8-sig")  # handle BOM from Excel
    except UnicodeDecodeError:
        raise ValueError("File must be UTF-8 encoded.")

    reader = csv.DictReader(io.StringIO(text))

    # Normalise header names: strip whitespace, lowercase
    if reader.fieldnames is None:
        raise ValueError("CSV file appears to be empty or has no header row.")

    normalised_headers = {h.strip().lower() for h in reader.fieldnames}
    missing = REQUIRED_COLUMNS - normalised_headers
    if missing:
        raise ValueError(
            f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
            f"Expected: sequence_number, kit_code, short_code (and optionally treatment_arm)."
        )

    rows: list[ParsedRow] = []
    seen_sequence: set[int] = set()
    seen_kit_codes: set[str] = set()

    for line_num, raw_row in enumerate(reader, start=2):  # line 1 = header
        # Normalise keys
        row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items()}

        # --- sequence_number ---
        seq_str = row.get("sequence_number", "")
        if not seq_str:
            raise ValueError(f"Row {line_num}: 'sequence_number' is empty.")
        try:
            seq = int(seq_str)
        except ValueError:
            raise ValueError(
                f"Row {line_num}: 'sequence_number' must be an integer, got '{seq_str}'."
            )
        if seq < 1:
            raise ValueError(
                f"Row {line_num}: 'sequence_number' must be a positive integer, got {seq}."
            )
        if seq in seen_sequence:
            raise ValueError(
                f"Row {line_num}: duplicate 'sequence_number' {seq} in this file."
            )
        seen_sequence.add(seq)

        # --- kit_code ---
        kit_code = row.get("kit_code", "")
        if not kit_code:
            raise ValueError(f"Row {line_num}: 'kit_code' is empty.")
        if kit_code in seen_kit_codes:
            raise ValueError(
                f"Row {line_num}: duplicate 'kit_code' '{kit_code}' in this file."
            )
        seen_kit_codes.add(kit_code)

        # --- short_code ---
        short_code = row.get("short_code", "")
        if not short_code:
            raise ValueError(f"Row {line_num}: 'short_code' is empty.")

        # --- treatment_arm (optional display name) ---
        treatment_name = row.get("treatment_arm", "") or short_code

        rows.append(
            ParsedRow(
                sequence_number=seq,
                kit_code=kit_code,
                short_code=short_code,
                treatment_name=treatment_name,
            )
        )

    if not rows:
        raise ValueError("CSV file contains no data rows.")

    return rows
