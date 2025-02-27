#pdf_processing.py
import logging  # Import the logging module for structured logging
import os  # Import the os module for operating system-related tasks like file path manipulation
import PyPDF2  # Import the PyPDF2 library for reading and manipulating PDF files
from langchain.docstore.document import Document  # Import the Document class from LangChain for representing documents
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Import the RecursiveCharacterTextSplitter for splitting text into chunks
from langchain_community.vectorstores import FAISS  # Import FAISS for creating and managing vector stores
from langchain_huggingface import HuggingFaceEmbeddings  # Import HuggingFaceEmbeddings for generating embeddings


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')  # Configure basic logging settings

# Step 1: Read the PDF
def read_pdf(file):
    """Reads a PDF file and extracts the text."""
    try:
        reader = PyPDF2.PdfReader(file)  # Create a PdfReader object to read the PDF file
        if reader.is_encrypted:  # Check if the PDF is encrypted
            try:
                reader.decrypt("")  # Attempt to decrypt the PDF with an empty password
                logging.info(f"Successfully decrypted PDF: {file.name}") # Log successful decryption
            except Exception as e:
                logging.error(f"Cannot decrypt the PDF {file.name}: {str(e)}") # Log decryption failure
                raise ValueError(f"Cannot decrypt the PDF {file.name}: {str(e)}") # Raise a ValueError if decryption fails

        text = ""  # Initialize an empty string to store the extracted text
        for page_num in range(len(reader.pages)):  # Iterate through each page of the PDF
            try:
                page = reader.pages[page_num]  # Get the current page
                page_text = page.extract_text()  # Extract the text from the page
                if page_text:  # Check if the extracted text is not empty
                    text += page_text  # Append the extracted text to the 'text' string
            except Exception as e:
                logging.error(f"Error reading page {page_num}: {str(e)}") # Log error reading specific page

        if not text:
            logging.warning(f"No text extracted from the PDF: {file.name}") # Log if no text extracted
            raise ValueError("No text extracted from the PDF.") # Raise an error if no text was extracted

        logging.info(f"Successfully read PDF: {file.name}") # Log successful PDF reading
        return text  # Return the extracted text

    except PyPDF2.errors.PdfReadError as e:
        logging.error(f"Error reading the PDF file {file.name}: {str(e)}") # Log specific PyPDF2 error
        raise ValueError(f"Error reading the PDF file {file.name}: {str(e)}") # Raise a ValueError for PDF read errors
    except Exception as e:
        logging.error(f"An unexpected error occurred while reading the PDF: {str(e)}") # Log other unexpected errors
        raise Exception(f"An unexpected error occurred while reading the PDF: {str(e)}") # Raise a general exception for unexpected errors

# Step 2: Convert text to documents
def convert_to_documents(text):
    """Converts a text string to a list of LangChain Document objects."""
    try:
        if not text:
            logging.warning("Text content is empty, cannot convert to documents.") # Log if text is empty
            raise ValueError("Text content is empty, cannot convert to documents.") # Raise error if text is empty
        doc = Document(page_content=text)  # Create a LangChain Document object from the text
        logging.info("Successfully converted text to documents.") # Log successful conversion
        return [doc]  # Return a list containing the Document object
    except Exception as e:
        logging.error(f"Error converting text to document: {str(e)}") # Log error during document conversion
        raise Exception(f"Error converting text to document: {str(e)}") # Raise exception during document conversion

# Step 3: Split the document into chunks
def process_documents(documents):
    """Splits a list of LangChain Document objects into smaller chunks."""
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=550, chunk_overlap=50) # Initialize text splitter to chunk documents
        split_documents = text_splitter.split_documents(documents) # Split the documents into smaller chunks
        logging.info(f"Successfully split documents into {len(split_documents)} chunks.") # Log the number of chunks created
        return split_documents  # Return the list of split documents
    except Exception as e:
        logging.error(f"Error splitting documents: {str(e)}") # Log error during document splitting
        raise Exception(f"Error splitting documents: {str(e)}") # Raise exception during document splitting

# Step 4: Combine add_to_vector_store and generate_pdf_vectors
def add_to_vector_store_and_generate_vectors(documents, client_id, pdf_name, base_save_path):
    """
    Adds documents to a FAISS vector store, generates embeddings, and saves the store.
    Returns the vector store and the generated vectors.
    """
    try:
        embedding_function = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2') # Initialize embedding function
        vector_store = FAISS.from_documents(documents, embedding_function) # Create FAISS vector store from documents

        client_save_path = os.path.join(base_save_path, f'client_{client_id}') # Create client-specific save path
        os.makedirs(client_save_path, exist_ok=True) # Create directory if it doesn't exist

        faiss_index_file = os.path.join(client_save_path, pdf_name) # Create path to save FAISS index
        vector_store.save_local(faiss_index_file) # Save FAISS index
        logging.info(f"FAISS index saved to {faiss_index_file} for client {client_id}") # Log saved index

        vectors = vector_store.index.reconstruct_n(0, vector_store.index.ntotal) # Reconstruct all vectors from the index
        logging.info(f"Successfully generated vectors for client {client_id}") # Log vector generation
        return vector_store, vectors # Return the vector store and generated vectors

    except Exception as e:
        logging.error(f"Error adding documents to vector store and generating vectors for client {client_id}: {str(e)}") # Log error during vector store creation
        raise Exception(f"Error adding documents to vector store and generating vectors for client {client_id}: {str(e)}") # Raise exception during vector store creation