import asynctest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
import logging

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from extensions
from extensions.microsoft365 import microsoft365

class TestMicrosoft365Todo(asynctest.TestCase):
    def setUp(self):
        self.m365 = microsoft365(
            M365_CLIENT_ID="your_client_id",
            M365_CLIENT_SECRET="your-client-secret",
            M365_TENANT_ID="your-tenant-id"
        )
        logging.basicConfig(level=logging.DEBUG)

    @patch('extensions.microsoft365.microsoft365.authenticate')
    async def test_get_todo_tasks(self, mock_authenticate):
        logging.info("Testing get_todo_tasks method")

        # Set up mock objects
        mock_account = MagicMock()
        mock_tasks = MagicMock()
        mock_default_list = MagicMock()
        mock_task = MagicMock()

        # Configure mock behavior
        mock_authenticate.return_value = mock_account
        mock_account.tasks.return_value = mock_tasks
        mock_tasks.get_default_list.return_value = mock_default_list
        mock_default_list.get_tasks.return_value = [mock_task]

        # Set up mock task data
        mock_task.task_id = "task1"
        mock_task.subject = "Test Task"
        mock_task.body = "Test Body"
        mock_task.due = datetime.now() + timedelta(days=1)
        mock_task.completed = None

        # Call the method
        result = await self.m365.get_todo_tasks(max_tasks=1)

        # Assertions
        logging.info("Verifying method calls")
        mock_account.tasks.assert_called_once()
        mock_tasks.get_default_list.assert_called_once()
        mock_default_list.get_tasks.assert_called_once_with(limit=1)

        logging.info("Verifying result")
        self.assertEqual(len(result), 1, "Expected 1 task in the result")
        self.assertEqual(result[0]['id'], "task1", "Task ID mismatch")
        self.assertEqual(result[0]['title'], "Test Task", "Task title mismatch")
        self.assertEqual(result[0]['body'], "Test Body", "Task body mismatch")
        self.assertFalse(result[0]['completed'], "Task should not be completed")

        logging.info("get_todo_tasks test completed successfully")

    @patch('extensions.microsoft365.microsoft365.authenticate')
    async def test_create_todo_task(self, mock_authenticate):
        logging.info("Testing create_todo_task method")

        # Set up mock objects
        mock_account = MagicMock()
        mock_tasks = MagicMock()
        mock_default_list = MagicMock()
        mock_task = MagicMock()

        # Configure mock behavior
        mock_authenticate.return_value = mock_account
        mock_account.tasks.return_value = mock_tasks
        mock_tasks.get_default_list.return_value = mock_default_list
        mock_default_list.new_task.return_value = mock_task

        # Set up task data
        title = "New Task"
        body = "New Task Body"
        due_date = datetime.now() + timedelta(days=2)

        # Call the method
        result = await self.m365.create_todo_task(title, body, due_date)

        # Assertions
        logging.info("Verifying method calls")
        mock_account.tasks.assert_called_once()
        mock_tasks.get_default_list.assert_called_once()
        mock_default_list.new_task.assert_called_once()
        mock_task.save.assert_called_once()

        logging.info("Verifying task properties")
        self.assertEqual(mock_task.subject, title, "Task title mismatch")
        self.assertEqual(mock_task.body, body, "Task body mismatch")
        self.assertEqual(mock_task.due, due_date, "Task due date mismatch")

        logging.info("Verifying result")
        self.assertEqual(result, "Todo task created successfully.", "Unexpected result message")

        logging.info("create_todo_task test completed successfully")

    @patch('extensions.microsoft365.microsoft365.authenticate')
    async def test_update_todo_task(self, mock_authenticate):
        logging.info("Testing update_todo_task method")

        # Set up mock objects
        mock_account = MagicMock()
        mock_tasks = MagicMock()
        mock_default_list = MagicMock()
        mock_task = MagicMock()

        # Configure mock behavior
        mock_authenticate.return_value = mock_account
        mock_account.tasks.return_value = mock_tasks
        mock_tasks.get_default_list.return_value = mock_default_list
        mock_default_list.get_task.return_value = mock_task

        # Set up task data
        task_id = "task1"
        new_title = "Updated Task"
        new_body = "Updated Body"
        new_due_date = datetime.now() + timedelta(days=3)

        # Call the method
        result = await self.m365.update_todo_task(task_id, new_title, new_body, new_due_date)

        # Assertions
        logging.info("Verifying method calls")
        mock_account.tasks.assert_called_once()
        mock_tasks.get_default_list.assert_called_once()
        mock_default_list.get_task.assert_called_once_with(task_id)
        mock_task.save.assert_called_once()

        logging.info("Verifying updated task properties")
        self.assertEqual(mock_task.subject, new_title, "Updated task title mismatch")
        self.assertEqual(mock_task.body, new_body, "Updated task body mismatch")
        self.assertEqual(mock_task.due, new_due_date, "Updated task due date mismatch")

        logging.info("Verifying result")
        self.assertEqual(result, "Todo task updated successfully.", "Unexpected result message")

        logging.info("update_todo_task test completed successfully")

    @patch('extensions.microsoft365.microsoft365.authenticate')
    async def test_delete_todo_task(self, mock_authenticate):
        logging.info("Testing delete_todo_task method")

        # Set up mock objects
        mock_account = MagicMock()
        mock_tasks = MagicMock()
        mock_default_list = MagicMock()
        mock_task = MagicMock()

        # Configure mock behavior
        mock_authenticate.return_value = mock_account
        mock_account.tasks.return_value = mock_tasks
        mock_tasks.get_default_list.return_value = mock_default_list
        mock_default_list.get_task.return_value = mock_task

        # Set up task data
        task_id = "task1"

        # Call the method
        result = await self.m365.delete_todo_task(task_id)

        # Assertions
        logging.info("Verifying method calls")
        mock_account.tasks.assert_called_once()
        mock_tasks.get_default_list.assert_called_once()
        mock_default_list.get_task.assert_called_once_with(task_id)
        mock_task.delete.assert_called_once()

        logging.info("Verifying result")
        self.assertEqual(result, "Todo task deleted successfully.", "Unexpected result message")

        logging.info("delete_todo_task test completed successfully")

if __name__ == '__main__':
    asynctest.main()