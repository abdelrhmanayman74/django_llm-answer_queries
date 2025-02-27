from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_and_process_pdfs, name='upload_and_process_pdfs'),  # Example URL pattern
    path('status/<str:task_id>',views.check_task_status, name="check_task_status")
]