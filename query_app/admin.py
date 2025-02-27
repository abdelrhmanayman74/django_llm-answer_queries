from django.contrib import admin
from .models import PDFDocument, ConversationHistory  # Import the correct models

# Register the PDFDocument model
@admin.register(PDFDocument)
class PDFDocumentAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'pdf_name', 'file_path')
    search_fields = ('client_id', 'pdf_name')
    list_filter = ('client_id',)

# Register the ConversationHistory model
@admin.register(ConversationHistory)
class ConversationHistoryAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'role', 'timestamp')
    search_fields = ('session_id', 'role', 'content')
    list_filter = ('role', 'timestamp')