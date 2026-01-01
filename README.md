# Dropbox Auto-Organizer 🤖

Automatically organize your Dropbox files by type, date, and custom rules using Python automation.

## Features ✨

- **Smart File Organization**: Automatically sorts photos, documents, videos, and temp files
- **Date-Based Organization**: Photos organized by year (extracted from filename)
- **Custom Rules**: Configure your own file patterns and folder destinations
- **Safe Operation**: Dry-run mode to preview changes before applying
- **Comprehensive Logging**: Track all file movements and errors
- **Schedulable**: Can be run automatically on a schedule

## What It Does 📁

The script scans your Dropbox root directory and organizes files into:
- **Photos Archive/** - All image files, organized by year
- **Documents & Files/** - PDFs, Word docs, text files
- **Temp Files/** - Temporary and sync files
- **Videos/** - Video files

## Quick Start 🚀

### 1. Get Dropbox Access Token

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click "Create App"
3. Choose "Scoped access" and "Full Dropbox" access
4. Name your app (e.g., "File Organizer")
5. Go to "Permissions" tab and enable:
   - `files.content.write`
   - `files.content.read`
   - `files.metadata.read`
6. Go to "Settings" tab and generate an access token

### 2. Install Dependencies

```bash
pip install dropbox
```

### 3. Set Up Configuration

Create a `config.json` file:

```json
{
  "dropbox_token": "YOUR_ACCESS_TOKEN_HERE",
  "folders": {
    "photos": "/Photos Archive",
    "documents": "/Documents & Files",
    "temp": "/Temp Files",
    "videos": "/Videos"
  },
  "file_patterns": {
    "photos": [".jpg", ".jpeg", ".png", ".gif", ".heic"],
    "documents": [".pdf", ".doc", ".docx", ".txt", ".md"],
    "temp": ["USER_SCOPED_TEMP", "_sync", ".tmp"],
    "videos": [".mp4", ".avi", ".mov", ".mkv"]
  },
  "organize_by_date": true,
  "date_pattern": "(20\\d{2})(\\d{2})(\\d{2})",
  "dry_run": true
}
```

**OR** set environment variable:
```bash
export DROPBOX_ACCESS_TOKEN="your_token_here"
```

### 4. Run the Script

**Test run (no changes made):**
```bash
python dropbox_organizer.py
```

**Actual run (moves files):**
Set `"dry_run": false` in config.json, then:
```bash
python dropbox_organizer.py
```

## Scheduling Automation ⏰

### On Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at midnight)
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\dropbox_organizer.py`

### On Mac/Linux (Cron)

Add to crontab:
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/script && python3 dropbox_organizer.py
```

### Using GitHub Actions (Cloud-based)

Create `.github/workflows/organize.yml`:

```yaml
name: Organize Dropbox
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  organize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install dropbox
      - name: Run organizer
        env:
          DROPBOX_ACCESS_TOKEN: ${{ secrets.DROPBOX_TOKEN }}
        run: python dropbox_organizer.py
```

## Configuration Options ⚙️

| Option | Description | Default |
|--------|-------------|----------|
| `dropbox_token` | Your Dropbox API access token | Required |
| `folders` | Destination folders for each file type | See config |
| `file_patterns` | File extensions/patterns to match | See config |
| `organize_by_date` | Organize photos by year | `true` |
| `date_pattern` | Regex pattern to extract dates | `(20\d{2})(\d{2})(\d{2})` |
| `dry_run` | Preview mode (doesn't move files) | `false` |

## Customization 🎨

### Add New File Type

```json
"file_patterns": {
  "music": [".mp3", ".wav", ".flac"]
},
"folders": {
  "music": "/Music Library"
}
```

### Custom Date Pattern

For files like `photo_2024_12_31.jpg`:
```json
"date_pattern": "(20\\d{2})_(\\d{2})_(\\d{2})"
```

## Logs 📋

All operations are logged to `dropbox_organizer.log`:
```
2025-12-31 21:00:00 - INFO - Successfully connected to Dropbox
2025-12-31 21:00:01 - INFO - Moved: /20240128_055543.jpg -> /Photos Archive/2024/20240128_055543.jpg
2025-12-31 21:00:05 - INFO - Organization complete! Processed 150 files, moved 120 files
```

## Safety Features 🛡️

- **Dry Run Mode**: Test before making changes
- **Error Handling**: Continues processing if individual files fail
- **Detailed Logging**: Track every operation
- **No Deletion**: Only moves files, never deletes

## Troubleshooting 🔧

**"Dropbox access token not found"**
- Ensure token is in config.json or environment variable

**"Failed to connect to Dropbox"**
- Check internet connection
- Verify token is still valid
- Check app permissions

**Files not moving**
- Check `dry_run` is set to `false`
- Verify file patterns match your files
- Check logs for specific errors

## License

MIT License - Feel free to modify and use!

## Contributing

Pull requests welcome! Please test thoroughly before submitting.

---

**Created with ❤️ to help organize your digital life**
