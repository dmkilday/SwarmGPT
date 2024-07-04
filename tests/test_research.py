# test_research.py

import unittest
from unittest.mock import Mock, patch
from research import Research

class TestResearch(unittest.TestCase):
    def setUp(self):
        self.research = Research("test_path", "http://test.com")

    @patch('research.requests.get')
    def test_search(self, mock_get):
        mock_response = Mock()
        mock_response.content = "<root><entry></entry></root>"
        mock_get.return_value = mock_response

        result = self.research.search("test term", 5)
        
        self.assertIsNotNone(result)
        mock_get.assert_called_once_with("http://test.com", params={
            "search_query": "all:test term",
            "start": 0,
            "max_results": 5
        })

    # Add more tests for other Research methods...