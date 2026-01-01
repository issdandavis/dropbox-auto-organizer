#!/usr/bin/env python3
"""
Dropbox Auto-Organizer
Automatically organizes files in Dropbox by type, date, and custom rules.
"""

import os
import re
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import dropbox
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import WriteMode, FolderMetadata, FileMetadata
import yaml
from dotenv import load_dotenv


class DropboxOrganizer:
    """Main class for organizing Dropbox files."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Dropbox organizer.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.dbx = self._connect_dropbox()
        self.stats = {
            'photos_moved': 0,
            'documents_moved': 0,
            'temp_moved': 0,
            'errors': 0,
            'skipped': 0
        }
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Error: Config file '{config_path}' not found.")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            sys.exit(1)
            
    def _setup_logging(self):
        """Set up logging configuration."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('log_file', 'dropbox_organizer.log')
        max_bytes = log_config.get('max_log_size_mb', 10) * 1024 * 1024
        backup_count = log_config.get('backup_count', 5)
        
        # Create logger
        self.logger = logging.getLogger('DropboxOrganizer')
        self.logger.setLevel(log_level)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def _connect_dropbox(self) -> dropbox.Dropbox:
        """Connect to Dropbox API.
        
        Returns:
            Dropbox client instance
        """
        # Load environment variables
        load_dotenv()
        
        access_token = os.getenv('DROPBOX_ACCESS_TOKEN')
        if not access_token:
            self.logger.error("DROPBOX_ACCESS_TOKEN not found in environment variables.")
            self.logger.error("Please create a .env file with your Dropbox access token.")
            sys.exit(1)
            
        try:
            dbx = dropbox.Dropbox(access_token)
            # Verify the token works
            dbx.users_get_current_account()
            self.logger.info("Successfully connected to Dropbox API")
            return dbx
        except AuthError as e:
            self.logger.error(f"Authentication error: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Error connecting to Dropbox: {e}")
            sys.exit(1)
            
    def _ensure_folder_exists(self, folder_path: str):
        """Ensure a folder exists in Dropbox, create if it doesn't.
        
        Args:
            folder_path: Path to the folder
        """
        if self.config.get('dry_run', False):
            self.logger.info(f"[DRY RUN] Would ensure folder exists: {folder_path}")
            return
            
        try:
            self.dbx.files_get_metadata(folder_path)
            self.logger.debug(f"Folder already exists: {folder_path}")
        except ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                try:
                    self.dbx.files_create_folder_v2(folder_path)
                    self.logger.info(f"Created folder: {folder_path}")
                except ApiError as create_error:
                    self.logger.error(f"Error creating folder {folder_path}: {create_error}")
            else:
                self.logger.error(f"Error checking folder {folder_path}: {e}")
                
    def _should_skip(self, file_path: str, file_name: str) -> bool:
        """Check if a file should be skipped.
        
        Args:
            file_path: Full path to the file
            file_name: Name of the file
            
        Returns:
            True if file should be skipped
        """
        skip_config = self.config.get('skip', {})
        
        # Check skip folders
        skip_folders = skip_config.get('folders', [])
        for folder in skip_folders:
            if folder in file_path:
                return True
                
        # Check skip files
        skip_files = skip_config.get('files', [])
        for skip_file in skip_files:
            if file_name == skip_file or file_name.startswith(skip_file):
                return True
                
        return False
        
    def _extract_year_from_filename(self, filename: str) -> Optional[str]:
        """Extract year from filename using pattern.
        
        Args:
            filename: Name of the file
            
        Returns:
            Year string if found, None otherwise
        """
        if not self.config['rules']['photos'].get('enabled', True):
            return None
            
        pattern = self.config['rules']['photos'].get('year_pattern', r'20\d{2}')
        match = re.search(pattern, filename)
        if match:
            return match.group(0)
        return None
        
    def _is_document(self, filename: str) -> bool:
        """Check if file is a document based on extension.
        
        Args:
            filename: Name of the file
            
        Returns:
            True if file is a document
        """
        if not self.config['rules']['documents'].get('enabled', True):
            return False
            
        extensions = self.config['rules']['documents'].get('extensions', [])
        file_ext = os.path.splitext(filename.lower())[1]
        return file_ext in extensions
        
    def _is_temp_file(self, filename: str) -> bool:
        """Check if file is a temp file based on patterns.
        
        Args:
            filename: Name of the file
            
        Returns:
            True if file is a temp file
        """
        if not self.config['rules']['temp'].get('enabled', True):
            return False
            
        patterns = self.config['rules']['temp'].get('patterns', [])
        for pattern in patterns:
            if pattern in filename:
                return True
        return False
        
    def _move_file(self, from_path: str, to_path: str) -> bool:
        """Move a file in Dropbox.
        
        Args:
            from_path: Source path
            to_path: Destination path
            
        Returns:
            True if successful, False otherwise
        """
        if self.config.get('dry_run', False):
            self.logger.info(f"[DRY RUN] Would move: {from_path} -> {to_path}")
            return True
            
        try:
            self.dbx.files_move_v2(from_path, to_path, autorename=True)
            self.logger.info(f"Moved: {from_path} -> {to_path}")
            return True
        except ApiError as e:
            self.logger.error(f"Error moving file {from_path} to {to_path}: {e}")
            self.stats['errors'] += 1
            return False
            
    def _organize_file(self, file_metadata: FileMetadata):
        """Organize a single file based on rules.
        
        Args:
            file_metadata: Dropbox file metadata
        """
        file_path = file_metadata.path_display
        file_name = file_metadata.name
        
        # Check if should skip
        if self._should_skip(file_path, file_name):
            self.logger.debug(f"Skipping: {file_path}")
            self.stats['skipped'] += 1
            return
            
        folders = self.config.get('folders', {})
        moved = False
        
        # Check if it's a photo with year
        year = self._extract_year_from_filename(file_name)
        if year and not moved:
            photos_folder = folders.get('photos', 'Photos Archive')
            year_folder = f"/{photos_folder}/{year}"
            self._ensure_folder_exists(f"/{photos_folder}")
            self._ensure_folder_exists(year_folder)
            new_path = f"{year_folder}/{file_name}"
            if self._move_file(file_path, new_path):
                self.stats['photos_moved'] += 1
                moved = True
                
        # Check if it's a document
        if not moved and self._is_document(file_name):
            documents_folder = folders.get('documents', 'Documents & Files')
            dest_folder = f"/{documents_folder}"
            self._ensure_folder_exists(dest_folder)
            new_path = f"{dest_folder}/{file_name}"
            if self._move_file(file_path, new_path):
                self.stats['documents_moved'] += 1
                moved = True
                
        # Check if it's a temp file
        if not moved and self._is_temp_file(file_name):
            temp_folder = folders.get('temp', 'Temp Files')
            dest_folder = f"/{temp_folder}"
            self._ensure_folder_exists(dest_folder)
            new_path = f"{dest_folder}/{file_name}"
            if self._move_file(file_path, new_path):
                self.stats['temp_moved'] += 1
                moved = True
                
    def scan_and_organize(self, path: str = ""):
        """Scan Dropbox directory and organize files.
        
        Args:
            path: Path to scan (empty string for root)
        """
        self.logger.info(f"Starting scan of Dropbox path: /{path}")
        
        if self.config.get('dry_run', False):
            self.logger.info("Running in DRY RUN mode - no files will be moved")
        
        try:
            # List all files in the directory
            result = self.dbx.files_list_folder(f"/{path}" if path else "", recursive=False)
            
            # Process files
            for entry in result.entries:
                if isinstance(entry, FileMetadata):
                    self._organize_file(entry)
                    
            # Handle pagination if there are more files
            while result.has_more:
                result = self.dbx.files_list_folder_continue(result.cursor)
                for entry in result.entries:
                    if isinstance(entry, FileMetadata):
                        self._organize_file(entry)
                        
        except ApiError as e:
            self.logger.error(f"Error scanning Dropbox: {e}")
            sys.exit(1)
            
    def print_summary(self):
        """Print summary of operations."""
        self.logger.info("=" * 60)
        self.logger.info("ORGANIZATION SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Photos moved: {self.stats['photos_moved']}")
        self.logger.info(f"Documents moved: {self.stats['documents_moved']}")
        self.logger.info(f"Temp files moved: {self.stats['temp_moved']}")
        self.logger.info(f"Files skipped: {self.stats['skipped']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        total_moved = (self.stats['photos_moved'] + 
                      self.stats['documents_moved'] + 
                      self.stats['temp_moved'])
        self.logger.info(f"Total files moved: {total_moved}")
        self.logger.info("=" * 60)


def main():
    """Main entry point for the script."""
    print("Dropbox Auto-Organizer")
    print("=" * 60)
    
    # Check for config file
    config_path = "config.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        
    # Create organizer and run
    try:
        organizer = DropboxOrganizer(config_path)
        organizer.scan_and_organize()
        organizer.print_summary()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
