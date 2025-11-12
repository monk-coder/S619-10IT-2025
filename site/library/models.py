from django.conf import settings
from django.db import models


class ReadingStatus(models.Model):
    slug = models.SlugField(max_length=50, unique=True)
    label = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["label"]

    def __str__(self) -> str:
        return self.label


class Book(models.Model):
    SOURCE_OPEN_LIBRARY = "open_library"
    SOURCE_GOOGLE_BOOKS = "google_books"
    SOURCE_CHOICES = [
        (SOURCE_OPEN_LIBRARY, "Open Library"),
        (SOURCE_GOOGLE_BOOKS, "Google Books"),
    ]

    external_id = models.CharField(max_length=128, unique=True)
    source = models.CharField(max_length=32, choices=SOURCE_CHOICES)
    title = models.CharField(max_length=255)
    authors = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=32, blank=True)
    description = models.TextField(blank=True)
    cover_url = models.URLField(blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    published_date = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ReadingEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reading_entries")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="entries")
    status = models.ForeignKey(ReadingStatus, on_delete=models.PROTECT, related_name="entries")
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    review = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="entries")
    started_at = models.DateField(null=True, blank=True)
    finished_at = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "book")
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.user} — {self.book}"


class ReadingNote(models.Model):
    entry = models.ForeignKey(ReadingEntry, on_delete=models.CASCADE, related_name="notes")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Note for {self.entry.book.title}"
