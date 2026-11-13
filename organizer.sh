#!/usr/bin/env bash

%
set -uo pipefail

WORK_DIR="$(pwd)"
ARCHIVE_DIR="$WORK_DIR/archive"
SOURCE="$WORK_DIR/grades.csv"
LOG_FILE="$WORK_DIR/organizer.log"

SOURCE_NAME="grades.csv"
TIMESTAMP="$(date '+%Y%m%d-%H%M%S')"
ARCHIVED_NAME="grades_${TIMESTAMP}.csv"
DESTINATION="$ARCHIVE_DIR/$ARCHIVED_NAME"


if [ -d "$ARCHIVE_DIR" ]; then
    echo "Archive directory already exists: $ARCHIVE_DIR"
elif [ -e "$ARCHIVE_DIR" ]; then
    echo "Error: '$ARCHIVE_DIR' exists but is not a directory." >&2
    echo "Rename or remove it, then run organizer.sh again." >&2
    exit 1
else
    if mkdir "$ARCHIVE_DIR"; then
        echo "Created archive directory: $ARCHIVE_DIR"
    else
        echo "Error: could not create '$ARCHIVE_DIR'." >&2
        echo "Check the permissions of '$WORK_DIR' and try again." >&2
        exit 1
    fi
fi


if [ ! -e "$SOURCE" ]; then
    echo "Error: grades.csv was not found in $WORK_DIR." >&2
    echo "Run organizer.sh from the folder that contains grades.csv." >&2
    exit 1
fi

if [ ! -f "$SOURCE" ]; then
    echo "Error: '$SOURCE' is not a regular file." >&2
    exit 1
fi

if [ ! -r "$SOURCE" ]; then
    echo "Error: '$SOURCE' is not readable." >&2
    echo "Check the file permissions and try again." >&2
    exit 1
fi


while [ -e "$DESTINATION" ]; do
    ARCHIVED_NAME="grades_${TIMESTAMP}_${counter}.csv"
    DESTINATION="$ARCHIVE_DIR/$ARCHIVED_NAME"
    counter=$((counter + 1))
done


if ! mv "$SOURCE" "$DESTINATION"; then
    echo "Error: could not move '$SOURCE' to '$DESTINATION'." >&2
    echo "Check the permissions of both folders and try again." >&2
    exit 1
fi
echo "Archived: $SOURCE_NAME -> archive/$ARCHIVED_NAME"


if ! touch "$SOURCE"; then
    echo "Error: the file was archived to '$DESTINATION', but a new empty" >&2
    echo "grades.csv could not be created in '$WORK_DIR'." >&2
    echo "Create it manually with: touch \"$SOURCE\"" >&2
    exit 1
fi
echo "Created new empty file: $SOURCE"


LOG_ENTRY="[$(date '+%Y-%m-%d %H:%M:%S')] Archived '$SOURCE_NAME' -> 'archive/$ARCHIVED_NAME'"
if ! printf '%s\n' "$LOG_ENTRY" >> "$LOG_FILE"; then
    echo "Error: the file was archived, but the entry could not be written" >&2
    echo "to '$LOG_FILE'. Check the file permissions." >&2
    exit 1
fi
echo "Logged: $LOG_ENTRY"
echo "Log file: $LOG_FILE"
