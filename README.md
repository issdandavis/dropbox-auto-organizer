# Dropbox Auto-Organizer

AI-powered script to automatically organize Dropbox files by type, date, and custom rules.

## Features

- 🔗 **Dropbox API Integration**: Secure connection to your Dropbox account
- 📁 **Automatic Organization**: 
  - Photos organized by year (detects 20XX pattern in filename)
  - Documents sorted by file type (.pdf, .docx, .txt, etc.)
  - Temp files moved to dedicated folder (USER_SCOPED_TEMP, _sync patterns)
- ⚙️ **Configurable Rules**: Customize organization rules via YAML configuration
- 📊 **Logging & Error Handling**: Comprehensive logging with rotation support
- 🔄 **Schedulable**: Can be automated with cron jobs or task schedulers
- 🧪 **Dry Run Mode**: Test organization without moving files

## Installation

1. Clone the repository:
```bash
git clone https://github.com/issdandavis/dropbox-auto-organizer.git
cd dropbox-auto-organizer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Dropbox API credentials:
   - Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
   - Create a new app (choose "Scoped access" and "Full Dropbox" access)
   - Generate an access token
   - Copy `.env.example` to `.env` and add your token:
   ```bash
   cp .env.example .env
   # Edit .env and add your DROPBOX_ACCESS_TOKEN
   ```

## Configuration

The `config.yaml` file contains all organization rules and settings:

```yaml
# Folder names for organizing files
folders:
  photos: "Photos Archive"
  documents: "Documents & Files"
  temp: "Temp Files"

# File organization rules
rules:
  photos:
    enabled: true
    year_pattern: "20\\d{2}"  # Matches 2000-2099
    
  documents:
    enabled: true
    extensions:
      - ".pdf"
      - ".docx"
      - ".txt"
      # Add more extensions as needed
      
  temp:
    enabled: true
    patterns:
      - "USER_SCOPED_TEMP"
      - "_sync"
      - ".tmp"

# Dry run mode (test without moving files)
dry_run: false
```

## Usage

### Basic Usage

Run the organizer on your Dropbox root directory:

```bash
python organize_dropbox.py
```

### Test Mode (Dry Run)

Test what would happen without actually moving files:

1. Set `dry_run: true` in `config.yaml`
2. Run the script:
```bash
python organize_dropbox.py
```

### Custom Configuration

Use a custom configuration file:

```bash
python organize_dropbox.py /path/to/custom-config.yaml
```

## Scheduling

### Linux/Mac (cron)

Run the organizer daily at 2 AM:

```bash
# Edit crontab
crontab -e

# Add this line:
0 2 * * * cd /path/to/dropbox-auto-organizer && /usr/bin/python3 organize_dropbox.py >> /var/log/dropbox-organizer.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create a new task
3. Set trigger (e.g., daily at 2 AM)
4. Set action: Run `python.exe` with argument `C:\path\to\organize_dropbox.py`

### Using systemd (Linux)

Create a systemd service and timer:

1. Create service file `/etc/systemd/system/dropbox-organizer.service`:
```ini
[Unit]
Description=Dropbox Auto Organizer
After=network.target

[Service]
Type=oneshot
User=your_username
WorkingDirectory=/path/to/dropbox-auto-organizer
ExecStart=/usr/bin/python3 /path/to/dropbox-auto-organizer/organize_dropbox.py

[Install]
WantedBy=multi-user.target
```

2. Create timer file `/etc/systemd/system/dropbox-organizer.timer`:
```ini
[Unit]
Description=Run Dropbox Organizer Daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

3. Enable and start:
```bash
sudo systemctl enable dropbox-organizer.timer
sudo systemctl start dropbox-organizer.timer
```

## Logging

Logs are written to `dropbox_organizer.log` by default. The log file includes:
- Timestamp for each operation
- Files moved and their destinations
- Errors and warnings
- Summary statistics

Log rotation is configured in `config.yaml`:
```yaml
logging:
  level: "INFO"
  log_file: "dropbox_organizer.log"
  max_log_size_mb: 10
  backup_count: 5
```

## Examples

### Example 1: Photo Organization

File: `vacation_2023_beach.jpg`
- Detected year: 2023
- Moved to: `/Photos Archive/2023/vacation_2023_beach.jpg`

### Example 2: Document Organization

File: `report.pdf`
- Detected type: Document (.pdf extension)
- Moved to: `/Documents & Files/report.pdf`

### Example 3: Temp File Cleanup

File: `USER_SCOPED_TEMP_abc123`
- Detected pattern: USER_SCOPED_TEMP
- Moved to: `/Temp Files/USER_SCOPED_TEMP_abc123`

## Customization

### Adding Custom File Types

Edit `config.yaml` to add more document extensions:

```yaml
rules:
  documents:
    extensions:
      - ".pdf"
      - ".docx"
      - ".csv"    # Add spreadsheets
      - ".zip"    # Add archives
```

### Adding Custom Temp Patterns

Add more temp file patterns:

```yaml
rules:
  temp:
    patterns:
      - "USER_SCOPED_TEMP"
      - "_sync"
      - "desktop.ini"
      - ".DS_Store"
```

### Skipping Specific Files or Folders

Prevent certain files/folders from being organized:

```yaml
skip:
  folders:
    - "Important Documents"
    - "Work Projects"
  files:
    - ".dropbox"
    - "README.md"
```

## Troubleshooting

### Authentication Error

**Problem**: `Authentication error` when running the script

**Solution**: 
- Verify your access token in `.env` is correct
- Check token hasn't expired
- Ensure you created an app with "Full Dropbox" access

### Files Not Moving

**Problem**: Script runs but files aren't moving

**Solution**:
- Check if `dry_run: true` in config.yaml
- Verify file patterns match your filenames
- Check logs for specific errors

### Permission Denied

**Problem**: Permission errors when creating folders

**Solution**:
- Ensure your Dropbox app has write permissions
- Check the app access level (should be "Full Dropbox")

## Security Notes

- Never commit your `.env` file to version control
- Keep your access token secure
- Consider using Dropbox's OAuth flow for production use
- Regularly rotate access tokens

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the logs for detailed error messages
