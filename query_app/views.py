import os
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, StreamingHttpResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import logging
import openai
from typing import List, Dict
from .models import PDFDocument, ConversationHistory  # Import the models

load_dotenv()  # Load environment variables from .env file

logger = logging.getLogger(__name__)

# Initialize embedding function globally (this is independent of the client)
embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

@api_view(['POST'])
@authentication_classes([TokenAuthentication])  # Add Token Authentication
@permission_classes([IsAuthenticated])  # Restrict access to authenticated users
def query_pdf(request):
    """
    Endpoint to handle user queries and return responses based on the indexed PDF.
    Supports conversation history and text streaming.
    """
    # Input validation
    if 'query' not in request.data or 'pdf_name' not in request.data or 'session_id' not in request.data:
        return HttpResponseBadRequest("Missing 'query', 'pdf_name', or 'session_id' parameter.")

    query = request.data['query']
    pdf_name = request.data['pdf_name']
    session_id = request.data['session_id']

    # Get the client_id from the authenticated user
    client_id = str(request.user.id)  # Use the authenticated user's ID as the client ID

    try:
        # Fetch the PDF document from the database
        pdf_document = PDFDocument.objects.filter(client_id=client_id, pdf_name=pdf_name).first()
        if not pdf_document:
            logger.info(f"No PDF document found for client_id={client_id}, pdf_name={pdf_name}")
            return JsonResponse({
                "error": "No PDF document found. Please upload a PDF file first."
            }, status=404)

        faiss_index_file = pdf_document.file_path

        if not os.path.exists(faiss_index_file):
            logger.error(f"FAISS index not found at {faiss_index_file}")
            return JsonResponse({
                "error": "FAISS index not found. Please generate the index for the uploaded PDF."
            }, status=404)

        # Load the FAISS index dynamically for the client
        faiss_index = FAISS.load_local(faiss_index_file, embedding_function, allow_dangerous_deserialization=True)
        logger.info(f"FAISS index loaded successfully for client_id={client_id}, pdf_name={pdf_name}")

        # 1. Embed the query using Sentence Transformers
        query_vector = embedding_function.embed_query(query)

        # 2. Verify dimensionality
        if len(query_vector) != faiss_index.index.d:
            return JsonResponse({
                "error": f"Dimensionality mismatch: Query vector has {len(query_vector)} dimensions, but FAISS index has {faiss_index.index.d} dimensions."
            }, status=500)

        # 3. Perform similarity search
        relevant_docs = faiss_index.similarity_search_by_vector(query_vector, k=3)

        # 4. Combine the relevant chunks into a single context
        context = "\n".join([doc.page_content for doc in relevant_docs])

        # 5. Add the user's query to the conversation history
        ConversationHistory.objects.create(
            session_id=session_id,
            role="user",
            content=f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
        )

        # 6. Send the query and context to OpenAI with streaming
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return JsonResponse({"error": "OpenAI API key not found."}, status=500)

        # Set the OpenAI API key
        openai.api_key = openai_api_key

        # Fetch conversation history from the database
        conversation_history = ConversationHistory.objects.filter(session_id=session_id).order_by('timestamp')
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        for entry in conversation_history:
            messages.append({"role": entry.role, "content": entry.content})

        # Use the new OpenAI API format with streaming
        response_stream = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Use a valid model
            messages=messages,
            max_tokens=512,
            temperature=0.5,
            stream=True,  # Enable streaming,
        )

        # 7. Stream the response back to the client
        def generate():
            full_response = ""
            for chunk in response_stream:
                if chunk.choices[0].delta.content:
                    chunk_content = chunk.choices[0].delta.content
                    full_response += chunk_content
                    yield chunk_content

            # Add the assistant's response to the conversation history
            ConversationHistory.objects.create(
                session_id=session_id,
                role="assistant",
                content=full_response
            )

        return StreamingHttpResponse(generate(), content_type="text/plain")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)  # Log the full traceback
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)