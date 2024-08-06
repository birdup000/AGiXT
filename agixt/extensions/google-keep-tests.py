import asynctest
from unittest.mock import patch, MagicMock
import sys
import os
import logging

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from extensions
from extensions.google import google

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TestGoogleKeep(asynctest.TestCase):
    def setUp(self):
        self.google = google(
            GOOGLE_CLIENT_ID="client_id",
            GOOGLE_CLIENT_SECRET="client_secret",
            GOOGLE_PROJECT_ID="test_project_id",
            GOOGLE_API_KEY="test_api_key",
            GOOGLE_SEARCH_ENGINE_ID="test_search_engine_id"
        )

    @patch('extensions.google.google.authenticate')
    @patch('extensions.google.build')
    async def test_get_keep_notes(self, mock_build, mock_authenticate):
        logging.info("Starting test_get_keep_notes")
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_notes = MagicMock()
        mock_service.notes.return_value = mock_notes
        mock_notes.list.return_value.execute.return_value = {
            "notes": [
                {"name": "notes/note1", "title": "Test Note 1", "body": {"text": {"text": "Content 1"}}},
                {"name": "notes/note2", "title": "Test Note 2", "body": {"text": {"text": "Content 2"}}}
            ]
        }

        result = await self.google.get_keep_notes()
        logging.info(f"get_keep_notes result: {result}")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "note1")
        self.assertEqual(result[0]["title"], "Test Note 1")
        self.assertEqual(result[1]["id"], "note2")
        self.assertEqual(result[1]["content"], "Content 2")
        logging.info("test_get_keep_notes completed successfully")

    @patch('extensions.google.google.authenticate')
    @patch('extensions.google.build')
    async def test_create_keep_note(self, mock_build, mock_authenticate):
        logging.info("Starting test_create_keep_note")
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_notes = MagicMock()
        mock_service.notes.return_value = mock_notes
        mock_notes.create.return_value.execute.return_value = {"name": "notes/new_note_id"}

        title = "New Note"
        content = "This is a new note"

        result = await self.google.create_keep_note(title, content)
        logging.info(f"create_keep_note result: {result}")

        expected_body = {
            'title': title,
            'body': {
                'text': {
                    'text': content
                }
            }
        }
        mock_notes.create.assert_called_once_with(body=expected_body)
        self.assertEqual(result, "Note created successfully with ID: new_note_id")
        logging.info("test_create_keep_note completed successfully")

    @patch('extensions.google.google.authenticate')
    @patch('extensions.google.build')
    async def test_delete_keep_note(self, mock_build, mock_authenticate):
        logging.info("Starting test_delete_keep_note")
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_notes = MagicMock()
        mock_service.notes.return_value = mock_notes

        note_id = "note1"

        result = await self.google.delete_keep_note(note_id)
        logging.info(f"delete_keep_note result: {result}")

        mock_notes.delete.assert_called_once_with(name=f"notes/{note_id}")
        self.assertEqual(result, "Note deleted successfully.")
        logging.info("test_delete_keep_note completed successfully")

    @patch('extensions.google.google.authenticate')
    @patch('extensions.google.build')
    async def test_get_keep_notes_error(self, mock_build, mock_authenticate):
        logging.info("Starting test_get_keep_notes_error")
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_notes = MagicMock()
        mock_service.notes.return_value = mock_notes
        mock_notes.list.return_value.execute.side_effect = Exception("API Error")

        result = await self.google.get_keep_notes()
        logging.info(f"get_keep_notes_error result: {result}")

        self.assertEqual(result, [])
        logging.info("test_get_keep_notes_error completed successfully")

    @patch('extensions.google.google.authenticate')
    @patch('extensions.google.build')
    async def test_create_keep_note_error(self, mock_build, mock_authenticate):
        logging.info("Starting test_create_keep_note_error")
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_notes = MagicMock()
        mock_service.notes.return_value = mock_notes
        mock_notes.create.side_effect = Exception("API Error")

        result = await self.google.create_keep_note("Title", "Content")
        logging.info(f"create_keep_note_error result: {result}")

        self.assertEqual(result, "Failed to create note.")
        logging.info("test_create_keep_note_error completed successfully")

    @patch('extensions.google.google.authenticate')
    @patch('extensions.google.build')
    async def test_delete_keep_note_error(self, mock_build, mock_authenticate):
        logging.info("Starting test_delete_keep_note_error")
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_notes = MagicMock()
        mock_service.notes.return_value = mock_notes
        mock_notes.delete.side_effect = Exception("API Error")

        result = await self.google.delete_keep_note("note1")
        logging.info(f"delete_keep_note_error result: {result}")

        self.assertEqual(result, "Failed to delete note.")
        logging.info("test_delete_keep_note_error completed successfully")

if __name__ == '__main__':
    asynctest.main(verbosity=2)