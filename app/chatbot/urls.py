from django.urls import path
from . import views

urlpatterns = [
    path('', views.chatbot_view, name='chatbot_view'),
    path('chat/', views.chat_handler, name='chat_handler'),
    path('new_chat/', views.new_chat, name='new_chat'),
    path('pomato/', views.home_view, name='home_view'), 
    path('cart/', views.cart_view, name='cart_view'),
    path('brand/', views.brand_view, name='brand_view'),
    path('product/', views.product_view, name='product_view'),
    path('special/', views.special_view, name='special_view'),
    path('contact/', views.contact_view, name='contact_view'),
]
