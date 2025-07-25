from django.urls import path
from .views import get_text,logout_admin, download_any_base_file, download_any_txt_file, register_admin, login_admin, user_list, file_list,check_file,statistika,search_user,search_files, delete_user, create_user,delete_file, change_user, start_merge_task,check_merge_task_status, download_merged_zip

urlpatterns = [
   path('register/',register_admin,name='admin__register'),
   path('login/', login_admin, name='login_admin'),
   path('logout/', logout_admin, name='logout_admin'),
   path('users/',user_list, name='user_list'),
   path('files/', file_list, name='file_list'),
   path('verify/<uuid:uuid>/<str:value>/', check_file, name='check_file'),
   path('statistika/', statistika, name='statistika'),
   path('search_user/',search_user, name='search_user'),
   path('search_files/',search_files, name='search_file'),
   path('delete_user/<str:username>/',delete_user, name='delete_user'),
   path('create_user/', create_user, name='create_user'),
   path('delete_file/<uuid:uuid>/', delete_file, name='delete_file'),
   path('change_user/<int:user_id>', change_user, name='change_user'),
   path('download_admin_base/<uuid:uuid>/', download_any_base_file, name='download_any_base_file'),
   path('download_admin_txt/<uuid:uuid>/', download_any_txt_file, name='download_any_txt_file'),
   path('start_merge/', start_merge_task, name='download_merged_txt_files'),
   path('task_status/<str:task_id>',check_merge_task_status, name='check_merge_task_status'),
   path('download-merged/',download_merged_zip, name='download_merged_zip'),
   path('text/<uuid:uuid>/', get_text, name='get-text'),
]
