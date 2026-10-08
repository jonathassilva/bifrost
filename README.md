# Bifrost

Bifrost is an internal ThreatLab tool for automating the download of malware samples from the [VirusSign](https://www.virussign.com/) subscriber portal.

Given a target date, the script fetches the corresponding sample archives and metadata file from the VirusSign subscriber directory, organizing downloads locally by date.

---

## Requirements

- Python 3.10+
- [wget](https://www.gnu.org/software/wget/) available in PATH
  - **Linux**: `sudo apt install wget`
  - **Windows**: download from [eternallybored.org/misc/wget](https://eternallybored.org/misc/wget/) or install via `choco install wget`
- Python dependency:
  ```bash
  pip install beautifulsoup4
  ```

---

## Credentials

Create a file named `virussign.auth` inside `downloaders/` (same directory as the scripts). It must contain exactly two lines:

```
your_username
your_password
```

> **Important:** `virussign.auth` must be listed in `.gitignore`. Never commit credentials to version control.

---

## Usage

```bash
python downloaders/malwares_downloader.py 2026/05/19   # general malware feed
python downloaders/android_downloader.py  2026/05/19   # Android feed
```

Or using the named flag:

```bash
python downloaders/malwares_downloader.py --date 2026/05/19
```

The date can be given as `YYYY/MM/DD`, `YYYY-MM-DD` or `YYYYMMDD`.

To download several dates at once, see [`scripts/README.md`](scripts/README.md).

---

## Output

Downloads are saved to:

```
malwares-virus-sign/
└── 20260519/
    ├── virussign.com_20260519_B_Free.zip
    ├── virussign.com_20260519_B_Professional_01.zip.pgp
    ├── virussign.com_20260519_B_Standard_01.zip.pgp
    ├── virussign.com_20260519_Free.zip
    ├── virussign.com_20260519_Professional_01.zip.pgp
    ├── virussign.com_20260519_Standard_01.zip.pgp
    └── ... (metadata file included)
```

Interrupted downloads are automatically resumed on the next run (`--continue`).

---

## Recommended .gitignore

```gitignore
virussign.auth
malwares-virus-sign/
```

---

## Security Notes

- Always extract archives in an isolated VM or sandbox with no shared network with the host.
- Disable antivirus monitoring on the download directory before running, or samples will be deleted as they arrive.
- Do not use a cloud-synced folder (OneDrive, Google Drive, Dropbox) as the output directory.
- Archives are encrypted with the industry-standard password `infected`.
