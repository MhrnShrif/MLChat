from django.urls import path
from .views import *

urlpatterns = [
    path('', chat_view, name='chat_view'),
    path('api/send-message/', api_send_message, name='api_send_message'),
    path('api/clear-history/', clear_chat_history, name='clear_history'),
]
