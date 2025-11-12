from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Book, ReadingEntry, ReadingNote, ReadingStatus, Tag


class LibraryAPITestCase(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.me_url = reverse("current-user")
        self.entries_url = reverse("reading-entries-list")
        self.notes_url = reverse("reading-notes-list")
        self.status_to_read = ReadingStatus.objects.get(slug="to_read")
        self.status_reading = ReadingStatus.objects.get(slug="reading")

    def _register_user(self, username="reader", password="SecurePass123"):
        payload = {
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return payload

    def test_registration_and_authentication_flow(self):
        creds = self._register_user()

        me_response = self.client.get(self.me_url)
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["username"], creds["username"])

        logout_response = self.client.post(self.logout_url)
        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)

        login_response = self.client.post(self.login_url, creds, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_reading_entry_lifecycle(self):
        self._register_user()
        book_payload = {
            "external_id": "OL123W",
            "source": "open_library",
            "title": "Test Driven Development",
            "authors": "Kent Beck",
            "isbn": "9780321146533",
            "description": "",
            "cover_url": "",
            "page_count": 220,
            "published_date": "2003",
        }
        create_response = self.client.post(
            self.entries_url,
            {
                "book_data": book_payload,
                "status": self.status_to_read.slug,
                "rating": None,
                "review": "",
                "tag_names": ["техника", "разработка"],
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        entry_id = create_response.data["id"]
        self.assertTrue(Book.objects.filter(external_id=book_payload["external_id"]).exists())
        self.assertEqual(Tag.objects.count(), 2)

        patch_response = self.client.patch(
            reverse("reading-entries-detail", args=[entry_id]),
            {
                "status": self.status_reading.slug,
                "rating": 5,
                "review": "Отличная книга",
                "tag_names": ["техника", "практика"],
            },
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        entry = ReadingEntry.objects.get(pk=entry_id)
        self.assertEqual(entry.status, self.status_reading)
        self.assertEqual(entry.rating, 5)
        self.assertEqual(set(entry.tags.values_list("name", flat=True)), {"техника", "практика"})

        note_response = self.client.post(
            self.notes_url,
            {
                "entry_id": entry_id,
                "content": "Нужно перечитать главу про тесты.",
            },
            format="json",
        )
        self.assertEqual(note_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReadingNote.objects.filter(entry=entry).count(), 1)

        list_response = self.client.get(self.entries_url, {"search": "development"})
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)
        self.assertEqual(list_response.data["results"][0]["id"], entry_id)

        delete_note_response = self.client.delete(reverse("reading-notes-detail", args=[note_response.data["id"]]))
        self.assertEqual(delete_note_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ReadingNote.objects.filter(entry=entry).count(), 0)
