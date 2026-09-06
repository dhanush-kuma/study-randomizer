"""
Parse a pre-randomized sequence CSV and return validated rows.

Expected columns (case-insensitive, leading/trailing whitespace stripped):
    sequence_number  – positive integer, unique within the file
    kit_code         – the treatment kit identifier (same value repeats for
                       all rows belonging to the same treatment arm, e.g.
                       "KIT-DA" for every Drug A row)
    treatment_arm    – display name of the treatment arm (e.g. "Drug A")

Arm validation is intentionally NOT performed here; the caller decides
whether to cross-check against study arms.
"""

from __future__ import annotations

import csv
import io
from typing import TypedDict


REQUIRED_COLUMNS = {"sequence_number", "kit_code", "treatment_arm"}


class ParsedRow(TypedDict):
    sequence_number: int
    kit_code: str
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
            f"Expected: sequence_number, kit_code, treatment_arm."
        )

    rows: list[ParsedRow] = []
    seen_sequence: set[int] = set()

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

        # --- treatment_arm ---
        treatment_name = row.get("treatment_arm", "")
        if not treatment_name:
            raise ValueError(f"Row {line_num}: 'treatment_arm' is empty.")

        rows.append(
            ParsedRow(
                sequence_number=seq,
                kit_code=kit_code,
                treatment_name=treatment_name,
            )
        )

    if not rows:
        raise ValueError("CSV file contains no data rows.")

    return rows
