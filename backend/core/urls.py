from django.urls import path
from .views import RegisterView, LoginView, LogoutView, UserProfileView, ContactListView, ChatHistoryView, UserSearchView

urlpatterns = [
    path('auth/register', RegisterView.as_view(), name='register'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile', UserProfileView.as_view(), name='profile'),
    path('contacts/', ContactListView.as_view(), name='contacts'),
    path('messages/<int:user_id>/', ChatHistoryView.as_view(), name='chat-history'),
    path('search/', UserSearchView.as_view(), name='user-search'),
]
