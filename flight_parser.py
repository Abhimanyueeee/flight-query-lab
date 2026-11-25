"""Flight Schedule Parser and Query Tool - command-line entry point."""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "241ADB125"
FIRST_NAME = "Abhimanyujalan"
LAST_NAME = "Kaladevi-Shaju"


class RunError(Exception):
    """A runtime problem that should end the run with exit code 1."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight CSV files, store valid flights as JSON and run queries.")
    parser.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    parser.add_argument("-d", metavar="FOLDER", help="parse every .csv file in a folder")
    parser.add_argument("-j", metavar="FILE", help="load an existing JSON database")
    parser.add_argument("-a", metavar="FILE", help="airport list file (needed with -i and -d)")
    parser.add_argument("-o", metavar="FILE", help="output path for the JSON database (default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON file with queries to run")
    parser.add_argument("-r", metavar="FOLDER", help="folder for the response file (default: current folder)")
    return parser


def read_json(path: str, what: str):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        raise RunError(f"cannot read {what} '{path}': {e.strerror or e}")
    except ValueError:  # JSONDecodeError and UnicodeDecodeError
        raise RunError(f"{what} '{path}' is not valid JSON")
    except RecursionError:
        raise RunError(f"{what} '{path}' is nested too deeply")


def write_json(path: str, data) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
    except OSError as e:
        raise RunError(f"cannot write '{path}': {e.strerror or e}")


def find_csv_files(folder: str) -> list[str]:
    if not os.path.isdir(folder):
        raise RunError(f"folder '{folder}' does not exist")
    try:
        names = sorted(os.listdir(folder))
    except OSError as e:
        raise RunError(f"cannot read folder '{folder}': {e.strerror or e}")
    paths = [os.path.join(folder, n) for n in names
             if n.endswith(".csv") and os.path.isfile(os.path.join(folder, n))]
    if not paths:
        raise RunError(f"no .csv files found in '{folder}'")
    return paths


def parse_and_write(args) -> list[dict]:
    """The -i / -d branch: parse CSVs, write the database and errors.log."""
    if args.i:
        paths = [args.i]
    else:
        paths = find_csv_files(args.d)

    try:
        airports = load_airports(args.a)
    except OSError as e:
        raise RunError(f"cannot read airport file '{args.a}': {e.strerror or e}")
    except UnicodeDecodeError:
        raise RunError(f"airport file '{args.a}' is not valid UTF-8")

    try:
        records, errors = parse_files(paths, airports)
    except OSError as e:
        raise RunError(f"cannot read '{e.filename}': {e.strerror or e}")
    except UnicodeDecodeError:
        raise RunError("a CSV file is not valid UTF-8")

    db_path = args.o or "db.json"
    log_path = os.path.join(os.path.dirname(os.path.abspath(db_path)), "errors.log")

    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    handler = None
    try:
        try:
            handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        except OSError as e:
            raise RunError(f"cannot write '{log_path}': {e.strerror or e}")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)

        logger.info("%d valid flights, %d invalid rows", len(records), len(errors))
        for message in errors:
            logger.warning("%s", message)

        write_json(db_path, records)
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()

    print(f"{len(records)} valid flights written to {db_path}, "
          f"{len(errors)} invalid rows logged to {log_path}")
    return records


def load_database(path: str) -> list[dict]:
    db = read_json(path, "database file")
    if not isinstance(db, list) or not all(isinstance(r, dict) for r in db):
        raise RunError(f"database file '{path}' must be a JSON array of objects")
    return db


def run(args) -> int:
    queries = None
    if args.q:
        queries = read_json(args.q, "query file")
        if not isinstance(queries, (dict, list)):
            raise RunError(f"query file '{args.q}' must be an object or an array")

    if args.j:
        db = load_database(args.j)
    else:
        db = parse_and_write(args)

    if queries is not None:
        responses = run_queries(db, queries)
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
        write_json(os.path.join(args.r or ".", filename), responses)
        print(f"{len(responses)} query responses written to {filename}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2

    sources = [s for s in (args.i, args.d, args.j) if s is not None]
    try:
        if len(sources) != 1:
            parser.error("exactly one of -i, -d or -j is required")
        if args.j is None and args.a is None:
            parser.error("-a is required with -i and -d")
        if args.j is not None and args.o is not None:
            parser.error("-o cannot be used with -j")
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 2

    try:
        return run(args)
    except RunError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: unexpected problem ({type(e).__name__}: {e})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())