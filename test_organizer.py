#!/usr/bin/env python3
"""
Unit tests for Dropbox Auto-Organizer
Tests the file organization logic without requiring Dropbox credentials.
"""

import unittest
import os
import sys
import tempfile
import yaml
from unittest.mock import Mock, patch, MagicMock

# Import the organizer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from organize_dropbox import DropboxOrganizer


class TestDropboxOrganizer(unittest.TestCase):
    """Test cases for DropboxOrganizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.config_data = {
            'folders': {
                'photos': 'Photos Archive',
                'documents': 'Documents & Files',
                'temp': 'Temp Files'
            },
            'rules': {
                'photos': {
                    'enabled': True,
                    'year_pattern': r'20\d{2}'
                },
                'documents': {
                    'enabled': True,
                    'extensions': ['.pdf', '.docx', '.txt']
                },
                'temp': {
                    'enabled': True,
                    'patterns': ['USER_SCOPED_TEMP', '_sync', '.tmp']
                }
            },
            'logging': {
                'level': 'INFO',
                'log_file': 'test.log',
                'max_log_size_mb': 10,
                'backup_count': 5
            },
            'dry_run': True,
            'skip': {
                'folders': ['Photos Archive', 'Documents & Files'],
                'files': ['.dropbox']
            }
        }
        
        # Create temp config file
        self.temp_config = tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        )
        yaml.dump(self.config_data, self.temp_config)
        self.temp_config.close()
        
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_config.name):
            os.unlink(self.temp_config.name)
        if os.path.exists('test.log'):
            os.unlink('test.log')
            
    @patch.dict(os.environ, {'DROPBOX_ACCESS_TOKEN': 'test_token'})
    @patch('organize_dropbox.dropbox.Dropbox')
    def test_year_extraction(self, mock_dropbox):
        """Test year extraction from filenames."""
        # Mock Dropbox API
        mock_dbx = MagicMock()
        mock_dbx.users_get_current_account.return_value = Mock()
        mock_dropbox.return_value = mock_dbx
        
        organizer = DropboxOrganizer(self.temp_config.name)
        
        # Test valid year patterns
        self.assertEqual(organizer._extract_year_from_filename('photo_2023.jpg'), '2023')
        self.assertEqual(organizer._extract_year_from_filename('IMG_20240101.jpg'), '2024')
        self.assertEqual(organizer._extract_year_from_filename('vacation2022summer.png'), '2022')
        
        # Test invalid patterns
        self.assertIsNone(organizer._extract_year_from_filename('photo.jpg'))
        self.assertIsNone(organizer._extract_year_from_filename('image_1999.jpg'))
        self.assertIsNone(organizer._extract_year_from_filename('file_2100.jpg'))
        
    @patch.dict(os.environ, {'DROPBOX_ACCESS_TOKEN': 'test_token'})
    @patch('organize_dropbox.dropbox.Dropbox')
    def test_document_detection(self, mock_dropbox):
        """Test document file detection."""
        mock_dbx = MagicMock()
        mock_dbx.users_get_current_account.return_value = Mock()
        mock_dropbox.return_value = mock_dbx
        
        organizer = DropboxOrganizer(self.temp_config.name)
        
        # Test document files
        self.assertTrue(organizer._is_document('report.pdf'))
        self.assertTrue(organizer._is_document('document.docx'))
        self.assertTrue(organizer._is_document('notes.txt'))
        self.assertTrue(organizer._is_document('FILE.PDF'))  # Case insensitive
        
        # Test non-document files
        self.assertFalse(organizer._is_document('photo.jpg'))
        self.assertFalse(organizer._is_document('video.mp4'))
        self.assertFalse(organizer._is_document('archive.zip'))
        
    @patch.dict(os.environ, {'DROPBOX_ACCESS_TOKEN': 'test_token'})
    @patch('organize_dropbox.dropbox.Dropbox')
    def test_temp_file_detection(self, mock_dropbox):
        """Test temp file detection."""
        mock_dbx = MagicMock()
        mock_dbx.users_get_current_account.return_value = Mock()
        mock_dropbox.return_value = mock_dbx
        
        organizer = DropboxOrganizer(self.temp_config.name)
        
        # Test temp files
        self.assertTrue(organizer._is_temp_file('USER_SCOPED_TEMP_abc123'))
        self.assertTrue(organizer._is_temp_file('file_sync_temp'))
        self.assertTrue(organizer._is_temp_file('temp.tmp'))
        
        # Test non-temp files
        self.assertFalse(organizer._is_temp_file('document.pdf'))
        self.assertFalse(organizer._is_temp_file('photo.jpg'))
        
    @patch.dict(os.environ, {'DROPBOX_ACCESS_TOKEN': 'test_token'})
    @patch('organize_dropbox.dropbox.Dropbox')
    def test_skip_logic(self, mock_dropbox):
        """Test file skipping logic."""
        mock_dbx = MagicMock()
        mock_dbx.users_get_current_account.return_value = Mock()
        mock_dropbox.return_value = mock_dbx
        
        organizer = DropboxOrganizer(self.temp_config.name)
        
        # Test skipping files in skip folders
        self.assertTrue(organizer._should_skip('/Photos Archive/photo.jpg', 'photo.jpg'))
        self.assertTrue(organizer._should_skip('/Documents & Files/doc.pdf', 'doc.pdf'))
        
        # Test skipping specific files
        self.assertTrue(organizer._should_skip('/root/.dropbox', '.dropbox'))
        
        # Test not skipping regular files
        self.assertFalse(organizer._should_skip('/root/photo.jpg', 'photo.jpg'))
        self.assertFalse(organizer._should_skip('/root/document.pdf', 'document.pdf'))
        
    @patch.dict(os.environ, {'DROPBOX_ACCESS_TOKEN': 'test_token'})
    @patch('organize_dropbox.dropbox.Dropbox')
    def test_config_loading(self, mock_dropbox):
        """Test configuration file loading."""
        mock_dbx = MagicMock()
        mock_dbx.users_get_current_account.return_value = Mock()
        mock_dropbox.return_value = mock_dbx
        
        organizer = DropboxOrganizer(self.temp_config.name)
        
        # Verify config loaded correctly
        self.assertEqual(organizer.config['folders']['photos'], 'Photos Archive')
        self.assertEqual(organizer.config['folders']['documents'], 'Documents & Files')
        self.assertTrue(organizer.config['rules']['photos']['enabled'])
        self.assertIn('.pdf', organizer.config['rules']['documents']['extensions'])


if __name__ == '__main__':
    unittest.main()
