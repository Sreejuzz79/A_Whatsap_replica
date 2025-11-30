from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from .serializers import UserSerializer, RegisterSerializer, MessageSerializer, ContactSerializer
from chat.models import Message, Contact
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        print(f"DEBUG: Login attempt for username: '{username}', password: {repr(password)}")
        user = authenticate(username=username, password=password)
        if user:
            print(f"DEBUG: User authenticated: {user}")
            login(request, user)
            
            # Debug session info
            print(f"DEBUG: Session key after login: {request.session.session_key}")
            print(f"DEBUG: Session data: {dict(request.session.items())}")
            print(f"DEBUG: User is authenticated: {request.user.is_authenticated}")
            
            response = Response(UserSerializer(user).data)
            print(f"DEBUG: Response cookies: {response.cookies}")
            return response
        print("DEBUG: Authentication failed")
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'message': 'Logged out'})

@method_decorator(csrf_exempt, name='dispatch')
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        print(f"DEBUG: UserProfileView headers: {self.request.headers}")
        print(f"DEBUG: UserProfileView COOKIES: {self.request.COOKIES}")
        print(f"DEBUG: User: {self.request.user}")
        return self.request.user

    def update(self, request, *args, **kwargs):
        print(f"DEBUG: Profile update request data keys: {request.data.keys()}")
        if 'profile_picture' in request.data:
            print(f"DEBUG: Profile picture length: {len(request.data['profile_picture'])}")
        
        try:
            response = super().update(request, *args, **kwargs)
            print(f"DEBUG: Response status: {response.status_code}")
            if response.status_code >= 400:
                print(f"DEBUG: Validation errors: {response.data}")
            return response
        except Exception as e:
            print(f"DEBUG: Exception during update: {e}")
            raise e

@method_decorator(csrf_exempt, name='dispatch')
class ContactListView(generics.ListCreateAPIView):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Add contact logic
        username = self.request.data.get('username')
        try:
            contact_user = User.objects.get(username=username)
            if contact_user == self.request.user:
                raise Exception("Cannot add yourself")
            serializer.save(user=self.request.user, contact=contact_user)
        except User.DoesNotExist:
            raise Exception("User not found")

@method_decorator(csrf_exempt, name='dispatch')
class ChatHistoryView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        other_user_id = self.kwargs['user_id']
        return Message.objects.filter(
            Q(sender=self.request.user, receiver_id=other_user_id) |
            Q(sender_id=other_user_id, receiver=self.request.user)
        ).order_by('timestamp')

@method_decorator(csrf_exempt, name='dispatch')
class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        print(f"DEBUG: Search query: '{query}', User: {self.request.user}, Auth: {self.request.auth}")
        if not query:
            return User.objects.none()
        queryset = User.objects.filter(
            Q(username__icontains=query) | Q(full_name__icontains=query)
        ).exclude(id=self.request.user.id)
        print(f"DEBUG: Found {queryset.count()} users")
        return queryset
