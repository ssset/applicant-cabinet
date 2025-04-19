from django.urls import path
from .views import ChatListView, ChatDetailView, AvailableOrganizationsView

urlpatterns = [
    path('chats/', ChatListView.as_view(), name='chat_list'),
    path('chat-detail/', ChatDetailView.as_view(), name='chat_detail'),
    path('available-organizations/', AvailableOrganizationsView.as_view(), name='available_organizations'),
]