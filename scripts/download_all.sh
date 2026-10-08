#!/usr/bin/env bash

# download_all.sh
# Usage: ./download_all.sh --source malware|android

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
if [[ "$#" -lt 2 ]]; then
  echo "Usage: $0 --source <malware|android>"
  exit 1
fi

SOURCE=""
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --source)
      SOURCE="$2"
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

DATES_FILE="$SCRIPT_DIR/dates.txt"
LOG_FILE="$SCRIPT_DIR/download-$SOURCE.log"

if [[ ! -f "$DATES_FILE" ]]; then
  echo "Dates file not found: $DATES_FILE"
  exit 1
fi

while IFS= read -r DATE; do
  # Skip empty lines
  [[ -z "$DATE" ]] && continue
  python "$(dirname "$SCRIPT_DIR")/downloaders/$DOWNLOADER" --date "$DATE
done < "$DATES_FILE"

echo "Download completed. Log saved to $LOG_FILE"
