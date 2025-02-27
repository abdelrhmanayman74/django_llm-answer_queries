from django.test import TestCase
from unittest.mock import patch, MagicMock
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from uploadfile.tasks import process_pdf_task

class TestTasks(TestCase):
    def setUp(self):
        # Create a valid sample PDF file for testing
        self.sample_pdf_path = "sample.pdf"
        c = canvas.Canvas(self.sample_pdf_path, pagesize=letter)
        c.drawString(100, 750, "This is a sample PDF file.")
        c.save()

    def tearDown(self):
        # Clean up the sample PDF file
        if os.path.exists(self.sample_pdf_path):
            os.remove(self.sample_pdf_path)

    @patch("uploadfile.tasks.read_pdf")
    @patch("uploadfile.tasks.convert_to_documents")
    @patch("uploadfile.tasks.process_documents")
    @patch("uploadfile.tasks.add_to_vector_store_and_generate_vectors")
    def test_process_pdf_task_success(self, mock_add, mock_process, mock_convert, mock_read):
        """Test processing a valid PDF file."""
        # Mock the return values
        mock_read.return_value = "sample text"
        mock_convert.return_value = [MagicMock()]
        mock_process.return_value = [MagicMock()]
        mock_add.return_value = (MagicMock(), [1, 2, 3])

        # Call the task
        result = process_pdf_task(self.sample_pdf_path, client_id="12345", pdf_name="sample.pdf")

        # Assert the result
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["client_id"], "12345")
        self.assertEqual(result["vectors"], [1, 2, 3])

    @patch("uploadfile.tasks.read_pdf")
    def test_process_pdf_task_file_not_found(self, mock_read):
        """Test handling a missing PDF file."""
        mock_read.side_effect = FileNotFoundError("File not found")

        # Call the task with a non-existent file
        result = process_pdf_task("nonexistent.pdf", client_id="12345", pdf_name="sample.pdf")

        # Assert the result
        self.assertEqual(result["status"], "error")
        self.assertIn("File not found", result["error"])

    @patch("uploadfile.tasks.read_pdf")
    @patch("uploadfile.tasks.convert_to_documents")
    def test_process_pdf_task_conversion_error(self, mock_convert, mock_read):
        """Test handling an error during document conversion."""
        mock_read.return_value = "sample text"
        mock_convert.side_effect = Exception("Conversion error")

        # Call the task
        result = process_pdf_task(self.sample_pdf_path, client_id="12345", pdf_name="sample.pdf")

        # Assert the result
        self.assertEqual(result["status"], "error")
        self.assertIn("Conversion error", result["error"])

    @patch("uploadfile.tasks.read_pdf")
    @patch("uploadfile.tasks.convert_to_documents")
    @patch("uploadfile.tasks.process_documents")
    @patch("uploadfile.tasks.add_to_vector_store_and_generate_vectors")
    def test_process_pdf_task_vector_store_error(self, mock_add, mock_process, mock_convert, mock_read):
        """Test handling an error during vector store creation."""
        mock_read.return_value = "sample text"
        mock_convert.return_value = [MagicMock()]
        mock_process.return_value = [MagicMock()]
        mock_add.side_effect = Exception("Vector store error")

        # Call the task
        result = process_pdf_task(self.sample_pdf_path, client_id="12345", pdf_name="sample.pdf")

        # Assert the result
        self.assertEqual(result["status"], "error")
        self.assertIn("Vector store error", result["error"])