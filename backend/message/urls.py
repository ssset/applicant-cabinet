from django.urls import path
from .views import ChatListView, ChatDetailView

urlpatterns = [
    path('chats/', ChatListView.as_view(), name='chat_list'),
    path('chat-detail/', ChatDetailView.as_view(), name='chat_detail'),
]