# Download All Scripts

This directory contains two helper scripts that automate the execution of the Python downloaders located in the `downloaders/` folder.

## Scripts

- **download_all.sh** – Bash script for Unix‑like environments (Linux, macOS, WSL).
- **download_all.bat** – Windows batch script for Command Prompt.

## How to use

Both scripts expect a single argument `--source` that determines which downloader to run:

```
--source malware   # uses downloaders/malwares_downloader.py
--source android   # uses downloaders/android_downloader.py
```

The scripts read a file named `dates.txt` placed in the same directory. Each line of `dates.txt` must contain a date in the format `YYYY/MM/DD`. For every date, the appropriate Python downloader is invoked with the `--date` flag.

All output (stdout and stderr) from the Python scripts is appended to `download.log` in this directory, which can be inspected for any errors or download issues.

## Example

```bash
# Unix/Linux/macOS
./download_all.sh --source malware
```

```cmd
:: Windows Command Prompt
download_all.bat --source android
```

Make sure you have Python installed and that the `downloaders/` scripts are executable.
