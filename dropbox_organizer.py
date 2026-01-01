#!/usr/bin/env python3
"""
Dropbox Auto-Organizer
Automatically organizes Dropbox files by type, date, and custom rules
"""

import dropbox
import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dropbox_organizer.log'),
        logging.StreamHandler()
    ]
)

class DropboxOrganizer:
    def __init__(self, config_file='config.json'):
        """Initialize the Dropbox organizer with configuration"""
        self.config = self.load_config(config_file)
        self.dbx = self.connect_dropbox()
        
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning(f"Config file {config_file} not found. Using defaults.")
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration"""
        return {
            "dropbox_token": os.getenv('DROPBOX_ACCESS_TOKEN', ''),
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
            "organize_by_date": True,
            "date_pattern": r"(20\d{2})(\d{2})(\d{2})",
            "dry_run": False
        }
    
    def connect_dropbox(self):
        """Connect to Dropbox API"""
        token = self.config.get('dropbox_token')
        if not token:
            raise ValueError("Dropbox access token not found in config or environment")
        
        try:
            dbx = dropbox.Dropbox(token)
            dbx.users_get_current_account()
            logging.info("Successfully connected to Dropbox")
            return dbx
        except Exception as e:
            logging.error(f"Failed to connect to Dropbox: {e}")
            raise
    
    def create_folder_if_not_exists(self, folder_path):
        """Create folder in Dropbox if it doesn't exist"""
        try:
            self.dbx.files_get_metadata(folder_path)
            logging.info(f"Folder {folder_path} already exists")
        except dropbox.exceptions.ApiError:
            try:
                self.dbx.files_create_folder_v2(folder_path)
                logging.info(f"Created folder: {folder_path}")
            except Exception as e:
                logging.error(f"Failed to create folder {folder_path}: {e}")
    
    def extract_date_from_filename(self, filename):
        """Extract date from filename using regex pattern"""
        pattern = self.config.get('date_pattern', r"(20\d{2})(\d{2})(\d{2})")
        match = re.search(pattern, filename)
        if match:
            year = match.group(1)
            return year
        return None
    
    def get_file_type(self, filename):
        """Determine file type based on extension or pattern"""
        filename_lower = filename.lower()
        
        # Check temp file patterns first
        for pattern in self.config['file_patterns']['temp']:
            if pattern.lower() in filename_lower:
                return 'temp'
        
        # Check file extension
        for file_type, extensions in self.config['file_patterns'].items():
            if file_type == 'temp':
                continue
            for ext in extensions:
                if filename_lower.endswith(ext.lower()):
                    return file_type
        
        return None
    
    def organize_files(self):
        """Main function to organize files in Dropbox root"""
        logging.info("Starting file organization...")
        
        # Create necessary folders
        for folder_path in self.config['folders'].values():
            self.create_folder_if_not_exists(folder_path)
        
        try:
            # List all files in root directory
            result = self.dbx.files_list_folder('', recursive=False)
            files_processed = 0
            files_moved = 0
            
            for entry in result.entries:
                # Skip folders
                if isinstance(entry, dropbox.files.FolderMetadata):
                    continue
                
                files_processed += 1
                filename = entry.name
                current_path = entry.path_lower
                
                # Determine file type
                file_type = self.get_file_type(filename)
                
                if not file_type:
                    logging.info(f"Skipping unknown file type: {filename}")
                    continue
                
                # Determine destination folder
                dest_folder = self.config['folders'][file_type]
                
                # Add year subfolder for photos if organize_by_date is enabled
                if file_type == 'photos' and self.config.get('organize_by_date'):
                    year = self.extract_date_from_filename(filename)
                    if year:
                        dest_folder = f"{dest_folder}/{year}"
                        self.create_folder_if_not_exists(dest_folder)
                
                # Build destination path
                dest_path = f"{dest_folder}/{filename}"
                
                # Move file
                if self.config.get('dry_run'):
                    logging.info(f"[DRY RUN] Would move: {current_path} -> {dest_path}")
                    files_moved += 1
                else:
                    try:
                        self.dbx.files_move_v2(current_path, dest_path)
                        logging.info(f"Moved: {current_path} -> {dest_path}")
                        files_moved += 1
                    except dropbox.exceptions.ApiError as e:
                        logging.error(f"Failed to move {current_path}: {e}")
            
            logging.info(f"Organization complete! Processed {files_processed} files, moved {files_moved} files")
            
        except Exception as e:
            logging.error(f"Error during organization: {e}")
            raise

def main():
    """Main entry point"""
    try:
        organizer = DropboxOrganizer()
        organizer.organize_files()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
