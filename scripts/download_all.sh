#!/usr/bin/env bash

# download_all.sh
# Usage: ./download_all.sh --source malware|android
#
# Reads one date per line from dates.txt (YYYY/MM/DD or YYYYMMDD) and runs the
# matching downloader for each one. Output goes to the console AND is appended
# to download-<source>.log in this directory.

set -u

# Determine script and repository directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
if [[ "$#" -lt 2 ]]; then
  echo "Usage: $0 --source <malware|android>"
  exit 1
fi

SOURCE=""
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --source)
      SOURCE="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

if [[ "$SOURCE" != "malware" && "$SOURCE" != "android" ]]; then
  echo "Invalid source: $SOURCE"
  echo "Valid values are 'malware' or 'android'"
  exit 1
fi

# Choose downloader script
if [[ "$SOURCE" == "malware" ]]; then
  DOWNLOADER="malwares_downloader.py"
else
  DOWNLOADER="android_downloader.py"
fi

# Prefer python3 (many Linux distros don't ship a 'python' alias)
PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "Python not found in PATH (tried python3 and python)."
  exit 1
fi

DATES_FILE="$SCRIPT_DIR/dates.txt"
LOG_FILE="$SCRIPT_DIR/download-$SOURCE.log"

if [[ ! -f "$DATES_FILE" ]]; then
  echo "Dates file not found: $DATES_FILE"
  exit 1
fi

TOTAL=0
FAILED=0

# - fd 3 keeps the dates file away from the child processes' stdin
# - '|| [[ -n "$DATE" ]]' processes the last line even without a trailing newline
while IFS= read -r -u 3 DATE || [[ -n "$DATE" ]]; do
  DATE="${DATE%$'\r'}"                 # tolerate CRLF (file edited on Windows)
  DATE="${DATE//[[:space:]]/}"         # strip stray spaces/tabs
  [[ -z "$DATE" || "$DATE" == \#* ]] && continue   # skip blanks and comments

  TOTAL=$((TOTAL + 1))
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ===== $SOURCE :: $DATE =====" | tee -a "$LOG_FILE"

  "$PYTHON_BIN" "$REPO_ROOT/downloaders/$DOWNLOADER" --date "$DATE" 2>&1 | tee -a "$LOG_FILE"
  if [[ "${PIPESTATUS[0]}" -ne 0 ]]; then
    FAILED=$((FAILED + 1))
    echo "[warn] Downloader failed for $DATE" | tee -a "$LOG_FILE"
  fi
done 3< "$DATES_FILE"

echo "Download completed: $TOTAL date(s), $FAILED failure(s). Log saved to $LOG_FILE"
[[ "$FAILED" -eq 0 ]]
