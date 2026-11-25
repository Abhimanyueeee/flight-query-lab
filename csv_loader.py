"""Reading CSV files into flight records and error messages."""
import csv
import os

from validator import to_record, validate_row


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given.

    Return (records, errors):
      records - valid flight records, in input order
      errors  - one message per invalid row, in input order, formatted as
                "<file name>:<line number>: <ERROR_CODE> | <free text>"
                (base file name only, no timestamp or level, no newline)

    Also performs the DUPLICATE_FLIGHT check across all the files.
    Does not write any files and does not log anything itself.
    """
    records = []
    errors = []
    seen = set()  # (flight_id, departure_datetime) of valid rows so far

    for path in paths:
        name = os.path.basename(path)
        # newline="" lets the csv module handle \n and \r\n correctly
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for fields in reader:
                line_no = reader.line_num  # 1-based physical line number

                if line_no == 1:
                    continue  # header

                # Blank line: nothing on it, or only whitespace
                if not fields or (len(fields) == 1 and fields[0].strip() == ""):
                    continue

                # Comment line: first non-whitespace char is '#'
                if fields[0].strip().startswith("#"):
                    continue

                code = validate_row(fields, airports)
                if code is None:
                    record = to_record(fields)
                    key = (record["flight_id"], record["departure_datetime"])
                    if key in seen:
                        code = "DUPLICATE_FLIGHT"
                    else:
                        seen.add(key)
                        records.append(record)

                if code is not None:
                    original = ",".join(fields)
                    errors.append(f"{name}:{line_no}: {code} | {original}")

    return records, errors