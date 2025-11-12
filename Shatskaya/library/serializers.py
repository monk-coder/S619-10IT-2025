from typing import Any, Dict, List

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Book, ReadingEntry, ReadingNote, ReadingStatus, Tag


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует.")
        return value

    def validate_password(self, value: str) -> str:
        user = User(
            username=self.initial_data.get("username", ""),
            email=self.initial_data.get("email", ""),
        )
        try:
            validate_password(value, user=user)
        except DjangoValidationError as exc:
            messages = [self._translate_password_error(message) for message in exc.messages]
            raise serializers.ValidationError(" ".join(messages))
        return value

    @staticmethod
    def _translate_password_error(message: str) -> str:
        if "This password is too short" in message:
            return "Пароль слишком короткий — минимум 6 символов."
        if "too common" in message:
            return "Пароль слишком распространён. Попробуйте более уникальный вариант."
        if "entirely numeric" in message:
            return "Пароль не должен состоять только из цифр."
        if "too similar to the username" in message:
            return "Пароль не должен повторять имя пользователя."
        if "too similar to the email" in message:
            return "Пароль не должен совпадать с email."
        return message

    def create(self, validated_data: Dict[str, Any]) -> User:
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ReadingStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingStatus
        fields = ("slug", "label")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name")


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = (
            "id",
            "external_id",
            "source",
            "title",
            "authors",
            "isbn",
            "description",
            "cover_url",
            "page_count",
            "published_date",
        )


class BookInputSerializer(serializers.Serializer):
    external_id = serializers.CharField(max_length=128)
    source = serializers.ChoiceField(choices=Book.SOURCE_CHOICES)
    title = serializers.CharField(max_length=255)
    authors = serializers.CharField(max_length=255, required=False, allow_blank=True)
    isbn = serializers.CharField(max_length=32, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    cover_url = serializers.URLField(required=False, allow_blank=True)
    page_count = serializers.IntegerField(required=False, allow_null=True)
    published_date = serializers.CharField(max_length=32, required=False, allow_blank=True)


class ReadingNoteSerializer(serializers.ModelSerializer):
    entry_id = serializers.PrimaryKeyRelatedField(
        source="entry",
        queryset=ReadingEntry.objects.all(),
        write_only=True,
        required=True,
    )
    entry = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ReadingNote
        fields = ("id", "entry", "entry_id", "content", "created_at", "updated_at")
        read_only_fields = ("entry", "created_at", "updated_at")


class ReadingEntrySerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    book_data = BookInputSerializer(write_only=True, required=False)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, write_only=True
    )
    tags = TagSerializer(many=True, read_only=True)
    notes = ReadingNoteSerializer(many=True, read_only=True)
    status = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=ReadingStatus.objects.all(),
    )
    status_label = serializers.CharField(source="status.label", read_only=True)

    class Meta:
        model = ReadingEntry
        fields = (
            "id",
            "book",
            "book_data",
            "status",
            "status_label",
            "rating",
            "review",
            "tag_names",
            "tags",
            "started_at",
            "finished_at",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate_rating(self, value: int | None) -> int | None:
        if value is None:
            return value
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Оценка должна быть в диапазоне от 1 до 5.")
        return value

    def _upsert_book(self, payload: Dict[str, Any]) -> Book:
        book, created = Book.objects.get_or_create(
            external_id=payload["external_id"],
            defaults={**payload},
        )
        if not created:
            for field, value in payload.items():
                setattr(book, field, value)
            book.save(update_fields=list(payload.keys()))
        return book

    def _sync_tags(self, entry: ReadingEntry, tag_names: List[str]) -> None:
        tags = []
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name.strip())
            tags.append(tag)
        entry.tags.set(tags)

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> ReadingEntry:
        book_payload = validated_data.pop("book_data", None)
        if not book_payload:
            raise serializers.ValidationError({"book_data": "Необходимо передать данные книги."})
        tag_names = validated_data.pop("tag_names", [])
        book = self._upsert_book(book_payload)
        entry, _ = ReadingEntry.objects.update_or_create(
            user=self.context["request"].user,
            book=book,
            defaults=validated_data,
        )
        if tag_names:
            self._sync_tags(entry, tag_names)
        return entry

    @transaction.atomic
    def update(self, instance: ReadingEntry, validated_data: Dict[str, Any]) -> ReadingEntry:
        validated_data.pop("book_data", None)
        tag_names = validated_data.pop("tag_names", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if tag_names is not None:
            self._sync_tags(instance, tag_names)
        return instance
