# test_agent.py

import unittest
from unittest.mock import Mock, patch
from agent import Agent
from task import Task

class TestAgent(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.mock_research = Mock()
        self.mock_agent_list = []
        
        self.agent = Agent(
            log_file_path="test_log.txt",
            data_file_path="test_data",
            model="test_model",
            research_url="http://test.com",
            agent_list=self.mock_agent_list,
            client=self.mock_client,
            id=1,
            name="Test Agent",
            description="Test Description",
            research=self.mock_research
        )

    def test_receive_task_desc(self):
        task_id = self.agent.receive_task_desc("Test Task", "Test Description")
        self.assertEqual(len(self.agent.task_list), 1)
        self.assertEqual(self.agent.task_list[0].id, task_id)
        self.assertEqual(self.agent.task_list[0].title, "Test Task")
        self.assertEqual(self.agent.task_list[0].description, "Test Description")

@patch('agent.Agent.do')
@patch('agent.Agent.delegate')
@patch('agent.Agent.set_decomposability')
@patch('agent.Task')
def test_work(self, MockTask, mock_set_decomposability, mock_delegate, mock_do):
    mock_task = Mock()
    mock_task.id = 1
    mock_task.outcome = "Test Outcome"
    mock_task.run.return_value = (Mock(), Mock())  # Mock the return value of run()
    MockTask.return_value = mock_task
    
    self.agent.receive_task_desc("Test Task", "Test Description")
    outcome = self.agent.work(1)
    
    self.assertEqual(outcome, "Test Outcome")
    mock_task.run.assert_called_once()
    # Ensure decompose_or_do was called
    self.assertTrue(hasattr(mock_task, 'is_decomposable'))

    # Add more tests for other Agent methods...