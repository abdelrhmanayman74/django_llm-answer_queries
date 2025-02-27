import os
import uuid
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from rest_framework.decorators import api_view, parser_classes, authentication_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .tasks import process_pdf_task
from celery.result import AsyncResult
import logging

# Set up logging for this module
logger = logging.getLogger(__name__)

@api_view(['POST'])  # This view only accepts POST requests
@parser_classes([MultiPartParser])  # Parse multipart form data (file uploads)
@authentication_classes([TokenAuthentication])  # Require token-based authentication
@permission_classes([IsAuthenticated])  # Restrict access to authenticated users
def upload_and_process_pdfs(request):
    """
    View to upload PDFs and trigger background processing using Celery.
    """
    # Check if the request contains any files
    if 'pdfs' not in request.FILES:
        return HttpResponseBadRequest("No files were uploaded.")

    # Get the list of uploaded PDF files
    pdfs = request.FILES.getlist('pdfs')
    allowed_file_types = ['application/pdf']  # Only allow PDF files
    task_ids = []  # Store the IDs of the Celery tasks created
    client_id = str(request.user.id)  # Use the authenticated user's ID as the client ID

    # Process each uploaded PDF file
    for pdf in pdfs:
        # Check if the file is a valid PDF
        if pdf.content_type not in allowed_file_types:
            return HttpResponseBadRequest(f"File {pdf.name} is not a valid PDF.")

        try:
            # Create a temporary directory for storing uploaded PDFs
            temp_dir = settings.TEMP_PDFS_DIR  # Get the path from Django settings
            os.makedirs(temp_dir, exist_ok=True)  # Create the directory if it doesn't exist

            # Generate a unique filename for the uploaded PDF
            temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.pdf")

            # Save the uploaded PDF to the temporary file
            with open(temp_file_path, 'wb+') as destination:
                for chunk in pdf.chunks():  # Read the file in chunks
                    destination.write(chunk)  # Write each chunk to the file

            # Trigger the Celery task to process the PDF
            task = process_pdf_task.delay(temp_file_path, client_id=client_id, pdf_name=pdf.name)
            task_ids.append(task.id)  # Store the task ID
            logger.info(f"Task {task.id} dispatched for {pdf.name} by client {client_id}")

        except OSError as e:
            # Log and return an error if there's an issue creating the temporary directory
            logger.error(f"Error creating temporary directory: {e}")
            return JsonResponse({"error": f"Error creating temporary directory: {str(e)}"}, status=500)
        except Exception as e:
            # Log and return an error if there's an issue processing the PDF
            logger.error(f"Error processing {pdf.name}: {e}")
            return JsonResponse({"error": f"Error processing {pdf.name}: {str(e)}"}, status=500)

    # Return a success response with the list of task IDs
    return JsonResponse({
        "message": "PDFs are being processed in the background.",
        "task_ids": task_ids
    }, status=202)


@api_view(['GET'])  # This view only accepts GET requests
@authentication_classes([TokenAuthentication])  # Require token-based authentication
@permission_classes([IsAuthenticated])  # Restrict access to authenticated users
def check_task_status(request, task_id):
    """
    View to check the status of a Celery task.
    """
    # Get the result of the Celery task using the task ID
    task_result = AsyncResult(task_id)

    # Check if the task failed
    if task_result.failed():
        logger.error(f"Task {task_id} failed: {task_result.traceback}")
        return JsonResponse({"task_id": task_id, "status": task_result.status, "error": "Task failed"})

    # Return the task status and result
    return JsonResponse({
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result
    })