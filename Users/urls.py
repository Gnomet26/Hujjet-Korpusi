from django.urls import path
from .views import register, login, logout,change,profile
urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('change/',change, name='change'),
    path('profile/',profile,name='profile'),
]