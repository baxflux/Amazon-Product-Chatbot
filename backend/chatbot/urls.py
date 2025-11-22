from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_view, name='chatbot_view'),
    path('chat/', views.chat_handler, name='chat_handler'),
    path('new_chat/', views.new_chat, name='new_chat'),
]
