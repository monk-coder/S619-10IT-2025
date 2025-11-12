from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ReadingEntry, ReadingNote, ReadingStatus, Tag
from .serializers import (
    LoginSerializer,
    ReadingEntrySerializer,
    ReadingNoteSerializer,
    ReadingStatusSerializer,
    RegisterSerializer,
    TagSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            raise AuthenticationFailed("Неверные учетные данные.")
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ReadingStatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReadingStatus.objects.all()
    serializer_class = ReadingStatusSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return (
            Tag.objects.filter(entries__user=self.request.user)
            .distinct()
            .order_by("name")
        )


class ReadingEntryViewSet(viewsets.ModelViewSet):
    serializer_class = ReadingEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = (
            ReadingEntry.objects.filter(user=self.request.user)
            .select_related("book", "status")
            .prefetch_related("tags", "notes")
        )
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(book__title__icontains=search)
                | Q(book__authors__icontains=search)
                | Q(book__isbn__icontains=search)
                | Q(tags__name__icontains=search)
                | Q(review__icontains=search)
            )
        status_slug = self.request.query_params.get("status")
        if status_slug:
            queryset = queryset.filter(status__slug=status_slug)
        tag_name = self.request.query_params.get("tag")
        if tag_name:
            queryset = queryset.filter(tags__name__iexact=tag_name)
        return queryset.distinct()


class ReadingNoteViewSet(viewsets.ModelViewSet):
    serializer_class = ReadingNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReadingNote.objects.filter(entry__user=self.request.user).select_related("entry", "entry__book")

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        entry_field = serializer.fields.get("entry_id")
        if entry_field and self.request and self.request.user.is_authenticated:
            entry_field.queryset = self.request.user.reading_entries.all()
        return serializer

    def perform_create(self, serializer):
        entry = serializer.validated_data.get("entry")
        if entry.user != self.request.user:
            raise PermissionDenied("Недостаточно прав для добавления заметки.")
        serializer.save()

    def perform_update(self, serializer):
        entry = serializer.instance.entry
        if entry.user != self.request.user:
            raise PermissionDenied("Недостаточно прав для изменения заметки.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.entry.user != self.request.user:
            raise PermissionDenied("Недостаточно прав для удаления заметки.")
        instance.delete()
