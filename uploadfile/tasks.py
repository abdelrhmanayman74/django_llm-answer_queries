import os
import logging
from celery import shared_task
from django.conf import settings  # Import the settings module
from .pdf_processing import read_pdf, convert_to_documents, process_documents, add_to_vector_store_and_generate_vectors
from query_app.models import PDFDocument  # Import the PDFDocument model

logger = logging.getLogger(__name__)

@shared_task
def process_pdf_task(pdf_path, client_id, pdf_name):
    """
    Celery task to process a PDF file asynchronously.
    """
    try:
        logger.info(f"Starting to process PDF: {pdf_path}")

        # Step 1: Read the PDF content
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"File not found: {pdf_path}")

        with open(pdf_path, 'rb') as file:
            pdf_text = read_pdf(file)
            logger.info(f"Successfully read PDF: {pdf_path}")

        # Step 2: Convert PDF text to LangChain documents
        documents = convert_to_documents(pdf_text)
        logger.info("Successfully converted text to documents")

        # Step 3: Split the documents into chunks
        split_documents = process_documents(documents)
        logger.info(f"Successfully split documents into {len(split_documents)} chunks")

        # Step 4: Add to vector store and generate vectors
        vector_store, vectors = add_to_vector_store_and_generate_vectors(split_documents, client_id, pdf_name, base_save_path=settings.FAISS_INDICES_DIR)
        logger.info("Successfully added documents to vector store and generated vectors")

        # Step 5: Save the PDF metadata to the database
        client_save_path = os.path.join(settings.FAISS_INDICES_DIR, f'client_{client_id}')
        faiss_index_file = os.path.join(client_save_path, pdf_name)

        # Create a new PDFDocument entry
        PDFDocument.objects.create(
            client_id=client_id,
            pdf_name=pdf_name,
            file_path=faiss_index_file
        )
        logger.info(f"Saved PDF metadata to the database for client {client_id}, PDF {pdf_name}")

        # Clean up the temporary file
        os.remove(pdf_path)
        logger.info(f"Successfully cleaned up temporary file: {pdf_path}")

        return {
            "status": "success",
            "client_id": client_id,
            "vectors": vectors.tolist() if hasattr(vectors, 'tolist') else vectors
        }

    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }