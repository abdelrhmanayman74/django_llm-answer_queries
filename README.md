Django LLM Task API

This project is a Django-based API that integrates with Langchain and OpenAI to process PDF documents and answer user queries. It uses Docker for containerization and includes a Redis-based Celery worker for background task processing.
Table of Contents

    System Architecture
    Features
    Setup Instructions
    Running the Application
    API Endpoints
    Docker Setup


System Architecture
  Overview:
  The system is designed to handle PDF document processing and querying using Langchain and OpenAI. It consists of the following components:

    Django API: The main application that exposes RESTful endpoints for uploading PDFs, querying documents, and managing conversation history.

    Langchain Integration: Handles embedding PDF content, performing similarity searches, and generating responses using OpenAI's GPT models.

    Celery Worker: Processes background tasks (e.g., PDF processing) asynchronously using Redis as the message broker.

    Docker Containers: The application is containerized using Docker, with separate containers for the Django API, Redis, and Celery worker.

Architectural Diagram

+-------------------+       +-------------------+       +-------------------+
|                   |       |                   |       |                   |
|   Django API      |<----->|   Redis (Broker)  |<----->|   Celery Worker   |
|                   |       |                   |       |                   |
+-------------------+       +-------------------+       +-------------------+
        ^                                                      ^
        |                                                      |
        |                                                      |
+-------------------+       			       	+-------------------+
|                   |                                 	|                   |
|   Langchain       |                		       	|   PDF Processing  |
|   (Quering)       |              	       		|   (FAISS Index)   |
|                   |                                 	|                   |
+-------------------+       			       	+-------------------+



Features

    PDF Upload and Processing: Upload PDF files, extract text, and generate embeddings using Langchain.

    Querying: Query the indexed PDF content and get responses using OpenAI's GPT models.

    Conversation History: Maintain a history of user queries and assistant responses.

    Background Processing: Use Celery and Redis for asynchronous task processing.

    Dockerized Setup: Easily deploy the application using Docker.
    
    
    
 Setup Instructions:
	Prerequisites
		Docker and Docker Compose installed on your system.
		OpenAI API key.

Steps:
	1-Clone the Repository:
   	        git clone https://github.com/abdelrhmanayman74/django_llm-answer_queries.git
		cd django_llm-answer_queries

   	2- Set Up Environment Variables:
		OPENAI_API_KEY=your_openai_api_key_here
		there is a username and password as a superuser created if you want to visit admin page
		there is a token created for superuser to test authentication

	3-Build and Run the Docker Containers:
		docker-compose build
		docker-compose up	
		
		
 Running the Application

    1-Start the Application:
	docker-compose up (1-2 min to start all containers)

    2-Access the API:
       The API will be available at http://localhost:8000
	Upload PDFs:
		Use the /api/upload/ endpoint to upload PDF files.
	Query PDFs:
	        Use the /query_pdf/ endpoint to query the indexed PDF content.

API Endpoints
	Upload PDFs
		URL: /api/upload/
			Method: POST
		Headers:
			key = Authorization, Value = Token your_token_here  
			
		Body:
			key = pdfs  Value = The PDF file(s) to upload.
	
	Query PDFs
		URL: /api/query_pdf/
		Method: POST
	Headers:
		key = Authorization, Value = Token your_token_here
		Content-Type: application/json
	Body:
	    json
	    {
		"query": "What is the main topic?",
		"pdf_name": "example.pdf",
		"session_id": "67890"
	    }

Docker Setup
	Docker Compose Services

	    api:

		The Django API service.

		Exposes port 8000.

	    redis:

		Redis service for Celery task queuing.

		Exposes port 6379.

	    celery_worker:

		Celery worker for background task processing.

	Dockerfile
		The Dockerfile installs all necessary dependencies and sets up the Django application.
	
	
	
