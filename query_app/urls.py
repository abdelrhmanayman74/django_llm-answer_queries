from django.urls import path
from . import views


urlpatterns = [
    path('', views.query_pdf, name='query_pdf'),
]