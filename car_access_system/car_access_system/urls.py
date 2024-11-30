# car_access_system/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('recognition.urls')),  # Подключение URL-ов приложения recognition
]
