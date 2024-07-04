# test_utils.py

import unittest
from unittest.mock import mock_open, patch
import utils

class TestUtils(unittest.TestCase):
    @patch('utils.os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_write_to_file(self, mock_file, mock_makedirs):
        utils.write_to_file("test/path.txt", "test content")
        
        mock_makedirs.assert_called_once_with("test", exist_ok=True)
        mock_file.assert_called_once_with("test/path.txt", 'w')
        mock_file().write.assert_called_once_with("test content")

    # Add more tests for other utility functions...