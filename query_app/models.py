# models.py
from django.db import models

class PDFDocument(models.Model):
    """
    Model to store metadata about PDF files and their corresponding FAISS indices.
    """
    client_id = models.CharField(max_length=100, help_text="Unique identifier for the client.")
    pdf_name = models.CharField(max_length=255, help_text="Name of the PDF file.")
    file_path = models.CharField(max_length=255, help_text="Path to the FAISS index file.")

    def __str__(self):
        return f"{self.client_id} - {self.pdf_name}"

class ConversationHistory(models.Model):
    """
    Model to store conversation history for each user or session.
    """
    session_id = models.CharField(max_length=100, help_text="Unique identifier for the user session.")
    role = models.CharField(max_length=50, help_text="Role of the message sender (user or assistant).")
    content = models.TextField(help_text="Content of the message.")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Timestamp of the message.")

    def __str__(self):
        return f"{self.session_id} - {self.role} - {self.timestamp}"