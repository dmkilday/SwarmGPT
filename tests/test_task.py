# test_task.py

import unittest
from unittest.mock import Mock, patch
from task import Task

class TestTask(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.task = Task(
            client=self.mock_client,
            log_file_path="test_log.txt",
            id=1,
            title="Test Task",
            description="Test Description",
            agent_id=1,
            research_url="http://test.com"
        )

    @patch('task.time.sleep')  # To avoid actual sleeping in tests
    def test_wait_on_run(self, mock_sleep):
        mock_run = Mock()
        mock_run.status = "in_progress"
        mock_thread = Mock()
        
        def side_effect(*args, **kwargs):
            mock_run.status = "completed"
            return mock_run

        self.mock_client.beta.threads.runs.retrieve.side_effect = side_effect
        
        result = self.task.wait_on_run(mock_run, mock_thread, 0.1)
        
        self.assertEqual(result.status, "completed")
        mock_sleep.assert_called()

    # Add more tests for other Task methods...