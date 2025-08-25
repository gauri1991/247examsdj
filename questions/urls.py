from django.urls import path
from . import views

# Template views only - API endpoints moved to api_urls.py
urlpatterns = [
    path('', views.question_bank_list, name='question-bank-list'),
    path('banks/', views.question_bank_list, name='question-bank'),
    path('create-bank/', views.create_question_bank, name='create-question-bank'),
    path('bank/<uuid:bank_id>/', views.question_bank_detail, name='question-bank-detail'),
    path('bank/<uuid:bank_id>/edit/', views.edit_question_bank, name='edit-question-bank'),
    path('bank/<uuid:bank_id>/create/', views.create_question, name='create-question'),
    path('bank/<uuid:bank_id>/import/', views.import_questions, name='import-questions'),
    path('bank/<uuid:bank_id>/export/', views.export_questions, name='export-questions'),
    path('create/', views.create_question, name='create-question-standalone'),
    path('edit/<uuid:question_id>/', views.edit_question, name='edit-question'),
    path('delete/<uuid:question_id>/', views.delete_question, name='delete-question'),
    path('preview/<uuid:question_id>/', views.question_preview_api, name='question-preview-api'),
]