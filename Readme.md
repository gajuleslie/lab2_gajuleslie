# Lab 2 — ALU Transcript Generator

A Python program that reads a CSV file of assignment grades, validates it
against the ALU grading rules, produces a transcript summary (final grade, GPA,
PASS/FAIL and resubmission options), plus a Bash organizer that archives the
grades file and resets the workspace.

The Python program uses **only the standard library** (`csv`, `math`, `os`,
`sys`). No third-party packages are required.

## Project files

| File | Purpose |
| --- | --- |
| `grades.csv` | The course grade data (assignment, group, score, weight). |
| `grade-evaluator.py` | Validates the CSV, calculates GPA and status, and reports resubmissions. |
| `organizer.sh` | Archives `grades.csv`, creates a fresh empty `grades.csv`, and writes `organizer.log`. |
| `tests/` | Extra CSV fixtures and an automated cross-check script. |
| `Readme.md` | This file. |

## Requirements

- Python 3.8 or newer (`python3 --version`)
- Bash
- A terminal

## Grading rules implemented

| Rule | Requirement |
| --- | --- |
| Score range | Every score must be between **0 and 100**. |
| Total weight | All assignment weights must add up to **exactly 100**. |
| Formative weight | Formative weights must add up to **exactly 60**. |
| Summative weight | Summative weights must add up to **exactly 40**. |
| Final weight | `score × weight ÷ 100` for each assignment. |
| Total grade | Sum of all final weights (out of 100). |
| GPA | `(Total Grade ÷ 100) × 5.0`, shown to 3 decimal places. |
| Pass/Fail | Pass only when the student reaches **at least 50% in both** Formative and Summative categories. |
| Resubmission | Failed formative assignments (score **below 50**) with the **highest weight**. If several failed formatives share that highest weight, **all** are listed. |

## Part 1 — `grade-evaluator.py`

Run the program from the project folder:

```bash
python3 grade-evaluator.py
```

It prompts for the CSV filename (the example shown in the prompt is
`grades.csv`):

```text
Enter the name of the CSV file to process (e.g., grades.csv): grades.csv
```

### Sample output for the provided `grades.csv`

```text
--- Processing Grades ---

Assignment                           Category    Grade (%)  Weight  Final weight
--------------------------------------------------------------------------------
Quiz                                 Formative          85      20            17
Group Exercise                       Formative          40      20             8
Functions and Debugging Lab          Formative          45      20             9
Midterm Project - Simple Calculator  Summative          70      20            14
Final Project - Text-Based Game      Summative          60      20            12

Formatives (60):            34 / 60  (56.67%)
Summatives (40):            26 / 40  (65.00%)
Total Grade:                60 / 100
GPA:                        3.000
Status:                     PASSED
Available for resubmission: Group Exercise, Functions and Debugging Lab
```

### How the numbers are calculated

- Formatives: `(85×20 + 40×20 + 45×20) ÷ 100 = 34` out of 60 → **56.67%**
- Summatives: `(70×20 + 60×20) ÷ 100 = 26` out of 40 → **65.00%**
- Total grade: `34 + 26 = 60` out of 100
- GPA: `(60 ÷ 100) × 5.0 = 3.000`
- Status: both categories are at or above 50% → **PASSED**
- Resubmission: `Group Exercise` (40%) and `Functions and Debugging Lab` (45%)
  both failed and both carry the highest failed formative weight (20), so both
  are displayed.

### Error handling

Validation errors are printed with the row number and a description, and the
program exits with status `1`:

```text
Validation failed:
  - Row 2 ('Quiz'): score 105 is outside the allowed range. Scores must be between 0 and 100.
Fix the problem(s) above in the CSV file and run the program again.
```

```text
Validation failed:
  - Total weight is 90; it must add up to exactly 100 (Formative 60 + Summative 40).
  - Formative weights add up to 50; they must add up to exactly 60.
Fix the problem(s) above in the CSV file and run the program again.
```

Other handled cases:

- Empty filename, or a file that does not exist.
- A folder name instead of a file.
- Missing required columns (`assignment`, `group`, `score`, `weight`).
- Empty or non-numeric values in any required field.
- Invalid category names.
- Completely blank lines are skipped.
- An empty CSV with no assignment rows.
- Unreadable files or invalid CSV encoding.

The `group` column accepts `Formative`/`Summative` case-insensitively, and the
short forms `FA`/`SA` are also accepted.

## Part 2 — `organizer.sh`

Run it from the project folder (the folder that contains `grades.csv`):

```bash
./organizer.sh
```

Each run:

1. Creates `archive/` if it does not already exist.
2. Renames `grades.csv` to `grades_<YYYYMMDD-HHMMSS>.csv` and moves it into
   `archive/`.
3. Immediately creates a new, empty `grades.csv` in the current directory.
4. Appends the timestamp, original filename and archived filename to
   `organizer.log` (the log accumulates entries across runs).

Example run:

```text
Archive directory already exists: /path/to/lab2_username/archive
Archived: grades.csv -> archive/grades_20261104-120905.csv
Created new empty file: /path/to/lab2_username/grades.csv
Logged: [2026-11-04 12:09:05] Archived 'grades.csv' -> 'archive/grades_20261104-120905.csv'
Log file: /path/to/lab2_username/organizer.log
```

Example `organizer.log` after two runs:

```text
[2026-11-04 12:09:05] Archived 'grades.csv' -> 'archive/grades_20261104-120905.csv'
[2026-11-04 12:09:05] Archived 'grades.csv' -> 'archive/grades_20261104-120905_1.csv'
```

The script stops with a helpful message if `grades.csv` is missing, is not a
regular file, is unreadable, if `archive` exists but is not a directory, or if a
permission problem prevents archiving, resetting, or logging. If two runs happen
within the same second, a numeric suffix (`_1`, `_2`, …) prevents overwriting an
existing archive file.

## Testing

The automated cross-check script runs the evaluator against the provided data,
the ALU transcript sample, an invalid score, invalid weights and a missing file,
then tests the organizer in a temporary directory:

```bash
./tests/run_tests.sh
```

Expected result:

```text
Results: 12 passed, 0 failed.
```

### Cross-check against the ALU transcript structure

The sample transcript has five assignments:

| Assignment | Category | Grade (%) | Weight | Final weight |
| --- | --- | --- | --- | --- |
| Group Coding Lab | FA | 100 | 30 | 30 |
| Discussion Forum | FA | 45 | 15 | 6.75 |
| General Quiz | FA | 51 | 15 | 7.65 |
| Pre-Summative | SA | 55 | 10 | 5.5 |
| Individual Lab | SA | 90 | 30 | 27 |

Running the evaluator on `tests/transcript_sample.csv` produces exactly the
transcript values:

| Check | Expected |
| --- | --- |
| Formatives (60) | `44.4` (74.00%) |
| Summatives (40) | `32.5` (81.25%) |
| Total grade | `76.9` |
| GPA | `3.845` |
| Status | `PASSED` |
| Available for resubmission | `Discussion Forum` |

`Discussion Forum` is the only failed formative (45%) and carries the highest
failed-formative weight (15).

## Notes

- Both scripts are executable (`chmod +x`), but they can also be run with
  `python3 grade-evaluator.py` and `bash organizer.sh`.
- The evaluator exits with `0` after a successful evaluation, including when the
  student status is `FAILED`. It exits with `1` only when the input or the data
  is invalid.
- `organizer.sh` only touches files in the folder it is run from. Always run it
  from the project root so `grades.csv`, `archive/` and `organizer.log` stay
  together.
