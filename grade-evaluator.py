#!/usr/bin/env python3
"""
Lab 2: ALU Transcript Generator

Reads a CSV file of assignment grades, validates the data, calculates the
weighted final grade and GPA, determines PASS/FAIL status and identifies
failed formative assignment(s) eligible for resubmission.

Uses only the Python standard library (csv, math, os, sys).
"""

import csv
import math
import os
import sys

# ---------------------------------------------------------------------------
# Rules for the ALU grading scheme
# ---------------------------------------------------------------------------
TOTAL_WEIGHT = 100.0
FORMATIVE_WEIGHT = 60.0
SUMMATIVE_WEIGHT = 40.0
PASS_MARK = 50.0          # percentage required in EACH category
MAX_SCORE = 100.0
GPA_SCALE = 5.0
WEIGHT_TOLERANCE = 1e-9

FORMATIVE = "Formative"
SUMMATIVE = "Summative"

# Accept the short forms used in the ALU transcript (FA / SA) as well.
GROUP_ALIASES = {
    "formative": FORMATIVE,
    "fa": FORMATIVE,
    "summative": SUMMATIVE,
    "sa": SUMMATIVE,
}

REQUIRED_COLUMNS = ("assignment", "group", "score", "weight")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def error(message):
    """Print a user-facing error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def fmt(value, decimals=2):
    """
    Format a number without unnecessary trailing zeros.

    Examples: 100.0 -> '100', 6.75 -> '6.75', 44.4 -> '44.4'
    """
    rounded = round(float(value), decimals)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.{decimals}f}".rstrip("0").rstrip(".")


def parse_number(text, field, row_number):
    """Convert a CSV field to a float, raising a helpful ValueError."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        raise ValueError(
            f"Row {row_number}: {field} value '{text}' is not a number. "
            f"Enter a number such as 85 or 12.5."
        )
    if not math.isfinite(value):
        raise ValueError(
            f"Row {row_number}: {field} value '{text}' is not a valid number. "
            f"Enter a finite number such as 85 or 12.5."
        )
    return value


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------
def load_csv_data():
    """
    Prompt the user for a filename, check if it exists, and extract all
    fields into a list of dictionaries.
    """
    try:
        filename = input(
            "Enter the name of the CSV file to process (e.g., grades.csv): "
        ).strip()
    except EOFError:
        print()
        error("no filename was provided (end of input reached).")
        print("  Example: grades.csv", file=sys.stderr)
        sys.exit(1)

    if not filename:
        error("no filename was entered.")
        print("  Example: grades.csv", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(filename):
        error(f"the file '{filename}' was not found.")
        print(
            f"  Check that '{filename}' is in the same folder as this script "
            f"({os.path.dirname(os.path.abspath(__file__))}) and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.isfile(filename):
        error(f"'{filename}' is not a regular file.")
        print("  Please provide the path to a CSV file, e.g., grades.csv", file=sys.stderr)
        sys.exit(1)

    assignments = []
    problems = []

    try:
        with open(filename, mode="r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            # Map header names (lower-cased, stripped) to the original names.
            columns = {}
            for original in reader.fieldnames or []:
                if original is not None:
                    columns[original.strip().lower()] = original

            missing = [name for name in REQUIRED_COLUMNS if name not in columns]
            if missing:
                error(
                    f"'{filename}' is missing required column(s): "
                    f"{', '.join(missing)}."
                )
                print(
                    f"  Expected header: {','.join(REQUIRED_COLUMNS)}",
                    file=sys.stderr,
                )
                if reader.fieldnames:
                    print(
                        f"  Found header:    {','.join(reader.fieldnames)}",
                        file=sys.stderr,
                    )
                sys.exit(1)

            for row in reader:
                row_number = reader.line_num
                raw = {
                    name: row.get(columns[name])
                    for name in REQUIRED_COLUMNS
                }

                # Skip completely blank lines in the CSV.
                if all(
                    value is None or str(value).strip() == ""
                    for value in raw.values()
                ):
                    continue

                assignment = str(raw["assignment"]).strip()
                group_text = str(raw["group"]).strip()
                score_text = str(raw["score"]).strip()
                weight_text = str(raw["weight"]).strip()

                empty_fields = [
                    name
                    for name, value in (
                        ("assignment", assignment),
                        ("group", group_text),
                        ("score", score_text),
                        ("weight", weight_text),
                    )
                    if value == ""
                ]
                if empty_fields:
                    problems.append(
                        f"Row {row_number}: empty value(s) for "
                        f"{', '.join(empty_fields)}. Every assignment needs a "
                        f"name, group, score (0-100) and weight."
                    )
                    continue

                group = GROUP_ALIASES.get(group_text.lower())
                if group is None:
                    problems.append(
                        f"Row {row_number}: group '{group_text}' is invalid. "
                        f"Use 'Formative' or 'Summative' (FA/SA are also accepted)."
                    )
                    continue

                try:
                    score = parse_number(score_text, "score", row_number)
                    weight = parse_number(weight_text, "weight", row_number)
                except ValueError as exc:
                    problems.append(str(exc))
                    continue

                assignments.append(
                    {
                        "assignment": assignment,
                        "group": group,
                        "score": score,
                        "weight": weight,
                        "line": row_number,
                    }
                )

    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        error(f"could not read '{filename}': {exc}")
        print(
            "  Check that the file is a valid UTF-8 text CSV and that you "
            "have permission to read it.",
            file=sys.stderr,
        )
        sys.exit(1)

    if problems:
        print(
            f"\nThe CSV file '{filename}' could not be processed:",
            file=sys.stderr,
        )
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print("Fix the row(s) above and run the program again.", file=sys.stderr)
        sys.exit(1)

    if not assignments:
        error(f"'{filename}' does not contain any assignment records.")
        print(
            "  The file must have a header row and at least one assignment row.",
            file=sys.stderr,
        )
        sys.exit(1)

    return assignments


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_scores(data):
    """Return a list of problems with assignment scores."""
    problems = []
    for record in data:
        if not 0.0 <= record["score"] <= MAX_SCORE:
            problems.append(
                f"Row {record['line']} ('{record['assignment']}'): score "
                f"{fmt(record['score'])} is outside the allowed range. Scores "
                f"must be between 0 and 100."
            )
    return problems


def validate_weights(data):
    """Return a list of problems with assignment weights."""
    problems = []

    for record in data:
        if record["weight"] <= 0:
            problems.append(
                f"Row {record['line']} ('{record['assignment']}'): weight "
                f"{fmt(record['weight'])} must be greater than 0."
            )

    formative_total = sum(
        record["weight"] for record in data if record["group"] == FORMATIVE
    )
    summative_total = sum(
        record["weight"] for record in data if record["group"] == SUMMATIVE
    )
    total = formative_total + summative_total

    if not math.isclose(total, TOTAL_WEIGHT, abs_tol=WEIGHT_TOLERANCE):
        problems.append(
            f"Total weight is {fmt(total)}; it must add up to exactly "
            f"{fmt(TOTAL_WEIGHT)} (Formative "
            f"{fmt(FORMATIVE_WEIGHT)} + Summative {fmt(SUMMATIVE_WEIGHT)})."
        )
    if not math.isclose(
        formative_total, FORMATIVE_WEIGHT, abs_tol=WEIGHT_TOLERANCE
    ):
        problems.append(
            f"Formative weights add up to {fmt(formative_total)}; they must "
            f"add up to exactly {fmt(FORMATIVE_WEIGHT)}."
        )
    if not math.isclose(
        summative_total, SUMMATIVE_WEIGHT, abs_tol=WEIGHT_TOLERANCE
    ):
        problems.append(
            f"Summative weights add up to {fmt(summative_total)}; they must "
            f"add up to exactly {fmt(SUMMATIVE_WEIGHT)}."
        )

    return problems


# ---------------------------------------------------------------------------
# Calculation and reporting
# ---------------------------------------------------------------------------
def find_resubmissions(data):
    """
    Return the name(s) of failed formative assignments (< 50%) that carry the
    highest weight. If several share that weight, all of them are returned.
    """
    failed_formatives = [
        record
        for record in data
        if record["group"] == FORMATIVE and record["score"] < PASS_MARK
    ]
    if not failed_formatives:
        return []

    highest_weight = max(record["weight"] for record in failed_formatives)
    return [
        record["assignment"]
        for record in failed_formatives
        if math.isclose(record["weight"], highest_weight, abs_tol=WEIGHT_TOLERANCE)
    ]


def evaluate_grades(data):
    """
    Validate the records, calculate the weighted grade and GPA, determine the
    PASS/FAIL status and report any assignment eligible for resubmission.
    """
    print("\n--- Processing Grades ---")

    problems = validate_scores(data) + validate_weights(data)
    if problems:
        print("\nValidation failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "Fix the problem(s) above in the CSV file and run the program again.",
            file=sys.stderr,
        )
        sys.exit(1)

    formative = [record for record in data if record["group"] == FORMATIVE]
    summative = [record for record in data if record["group"] == SUMMATIVE]

    formative_weight = sum(record["weight"] for record in formative)
    summative_weight = sum(record["weight"] for record in summative)

    # Final weight of one assignment = score * weight / 100.
    formative_earned = sum(
        record["score"] * record["weight"] / 100.0 for record in formative
    )
    summative_earned = sum(
        record["score"] * record["weight"] / 100.0 for record in summative
    )

    total_grade = formative_earned + summative_earned
    gpa = (total_grade / 100.0) * GPA_SCALE

    formative_percent = formative_earned / formative_weight * 100.0
    summative_percent = summative_earned / summative_weight * 100.0
    passed = (
        formative_percent >= PASS_MARK and summative_percent >= PASS_MARK
    )

    # ---- Transcript table ------------------------------------------------
    name_width = max(
        [len("Assignment")] + [len(record["assignment"]) for record in data]
    )
    header = (
        f"{'Assignment':<{name_width}}  {'Category':<10}  {'Grade (%)':>9}  "
        f"{'Weight':>6}  {'Final weight':>12}"
    )
    print()
    print(header)
    print("-" * len(header))
    for record in data:
        final_weight = record["score"] * record["weight"] / 100.0
        print(
            f"{record['assignment']:<{name_width}}  "
            f"{record['group']:<10}  "
            f"{fmt(record['score']):>9}  "
            f"{fmt(record['weight']):>6}  "
            f"{fmt(final_weight):>12}"
        )

    # ---- Summary ---------------------------------------------------------
    print()
    print(
        f"{'Formatives (' + fmt(FORMATIVE_WEIGHT) + '):':<28}"
        f"{fmt(formative_earned)} / {fmt(formative_weight)}  "
        f"({formative_percent:.2f}%)"
    )
    print(
        f"{'Summatives (' + fmt(SUMMATIVE_WEIGHT) + '):':<28}"
        f"{fmt(summative_earned)} / {fmt(summative_weight)}  "
        f"({summative_percent:.2f}%)"
    )
    print(f"{'Total Grade:':<28}{fmt(total_grade)} / {fmt(TOTAL_WEIGHT)}")
    print(f"{'GPA:':<28}{gpa:.3f}")
    print(f"{'Status:':<28}{'PASSED' if passed else 'FAILED'}")

    resubmissions = find_resubmissions(data)
    if resubmissions:
        print(f"{'Available for resubmission:':<28}{', '.join(resubmissions)}")
    else:
        print(f"{'Available for resubmission:':<28}None")


def main():
    course_data = load_csv_data()
    evaluate_grades(course_data)


if __name__ == "__main__":
    main()
