#!/usr/bin/env bash
#
# run_tests.sh - cross-check grade-evaluator.py and organizer.sh.
#
# Run from anywhere:
#   ./tests/run_tests.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
EVALUATOR="$PROJECT_DIR/grade-evaluator.py"

cd "$PROJECT_DIR" || exit 1

pass=0
fail=0

check_evaluator() {
    local description="$1"
    local expected_status="$2"
    local expected_text="$3"
    local csv="$4"
    local output
    local status

    output=$(printf '%s\n' "$csv" | python3 "$EVALUATOR" 2>&1)
    status=$?

    if [ "$status" -eq "$expected_status" ] &&
       printf '%s' "$output" | grep -qF -- "$expected_text"; then
        echo "PASS: $description"
        pass=$((pass + 1))
    else
        echo "FAIL: $description"
        echo "      exit code: $status (expected $expected_status)"
        echo "      expected text: $expected_text"
        printf '%s\n' "$output" | sed 's/^/      /'
        fail=$((fail + 1))
    fi
}

echo "== grade-evaluator.py =="

check_evaluator "grades.csv total grade" 0 "GPA:                        3.000" "grades.csv"
check_evaluator "grades.csv PASSED status" 0 "Status:                     PASSED" "grades.csv"
check_evaluator "grades.csv highest-weight resubmission tie" 0 \
    "Available for resubmission: Group Exercise, Functions and Debugging Lab" "grades.csv"

check_evaluator "transcript sample GPA 3.845" 0 "GPA:                        3.845" \
    "tests/transcript_sample.csv"
check_evaluator "transcript sample PASSED status" 0 "Status:                     PASSED" \
    "tests/transcript_sample.csv"
check_evaluator "transcript sample resubmission" 0 \
    "Available for resubmission: Discussion Forum" "tests/transcript_sample.csv"

check_evaluator "FAILED status when a category is below 50%" 0 "Status:                     FAILED" \
    "tests/tie_resubmission.csv"
check_evaluator "all tied failed formatives are listed" 0 \
    "Available for resubmission: Quiz A, Quiz B" "tests/tie_resubmission.csv"

check_evaluator "score above 100 is rejected" 1 "score 105 is outside the allowed range" \
    "tests/invalid_score.csv"
check_evaluator "wrong category weights are rejected" 1 \
    "Formative weights add up to 50; they must add up to exactly 60" \
    "tests/invalid_weights.csv"
check_evaluator "missing file is reported" 1 "was not found" "no-such-file.csv"

echo
echo "== organizer.sh =="

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/organizer-test.XXXXXX")"
cp "$PROJECT_DIR/organizer.sh" "$tmpdir/"
printf 'assignment,group,score,weight\nQuiz,Formative,85,60\nFinal Exam,Summative,80,40\n' \
    > "$tmpdir/grades.csv"

organizer_status=0
(
    cd "$tmpdir" || exit 1
    bash ./organizer.sh > /dev/null 2>&1
) || organizer_status=$?

if [ "$organizer_status" -eq 0 ] &&
   [ -d "$tmpdir/archive" ] &&
   ls "$tmpdir"/archive/grades_*.csv > /dev/null 2>&1 &&
   [ -f "$tmpdir/grades.csv" ] &&
   [ ! -s "$tmpdir/grades.csv" ] &&
   [ -f "$tmpdir/organizer.log" ] &&
   grep -q "Archived 'grades.csv'" "$tmpdir/organizer.log"; then
    echo "PASS: organizer archives, resets and logs"
    pass=$((pass + 1))
else
    echo "FAIL: organizer archives, resets and logs"
    fail=$((fail + 1))
fi

rm -rf "$tmpdir"

echo
echo "Results: $pass passed, $fail failed."
if [ "$fail" -ne 0 ]; then
    exit 1
fi
