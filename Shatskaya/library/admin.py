from django.contrib import admin

from .models import Book, ReadingEntry, ReadingNote, ReadingStatus, Tag


@admin.register(ReadingStatus)
class ReadingStatusAdmin(admin.ModelAdmin):
    list_display = ("label", "slug")
    search_fields = ("label", "slug")


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "authors", "isbn", "source")
    search_fields = ("title", "authors", "isbn")
    list_filter = ("source",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class ReadingNoteInline(admin.TabularInline):
    model = ReadingNote
    extra = 0


@admin.register(ReadingEntry)
class ReadingEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "status", "rating", "updated_at")
    search_fields = ("book__title", "book__authors", "user__username")
    list_filter = ("status", "tags")
    inlines = [ReadingNoteInline]
    filter_horizontal = ("tags",)


@admin.register(ReadingNote)
class ReadingNoteAdmin(admin.ModelAdmin):
    list_display = ("entry", "created_at")
    search_fields = ("entry__book__title", "content")
