from django.urls import path
from .views import set_or_edit_description,upload_file,update_text,get_text,download_base_file, check_file_status, download_txt_file, my_files,search_files,delete_file,verify_file

urlpatterns = [
    path('upload/', upload_file, name='upload_file'),
    path('status/<uuid:file_id>/',check_file_status, name='check_file_status'),
    path('my_files/', my_files, name='my_files'),
    path('search/', search_files, name='search_files'),
    path('delete/<uuid:uuid>', delete_file, name='delete_file'),
    path('download_base/<uuid:uuid>/', download_base_file, name='download_base'),
    path('download_txt/<uuid:uuid>/', download_txt_file, name='download_txt'),
    path('verify/<uuid:uuid>/<str:value>/', verify_file, name='verify_file'),
    path('text/<uuid:uuid>/', get_text, name='get-text'),
    path('update/',update_text, name='update_text'),
    path('description/<uuid:uuid>/', set_or_edit_description, name='set_or_edit_content')
    
] 