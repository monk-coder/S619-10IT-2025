from __future__ import annotations

import asyncio
import io
from dataclasses import dataclass

import pdfplumber
import pytesseract
from PIL import Image


@dataclass(slots=True)
class OCRService:
    language: str = "eng"

    async def extract_from_image(self, image_bytes: bytes) -> str:
        return await asyncio.to_thread(self._extract_from_image_sync, image_bytes)

    async def extract_from_pdf(self, pdf_bytes: bytes) -> str:
        return await asyncio.to_thread(self._extract_from_pdf_sync, pdf_bytes)

    def _extract_from_image_sync(self, image_bytes: bytes) -> str:
        with Image.open(io.BytesIO(image_bytes)) as image:
            return pytesseract.image_to_string(image, lang=self.language).strip()

    def _extract_from_pdf_sync(self, pdf_bytes: bytes) -> str:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            texts = [page.extract_text() or "" for page in pdf.pages]
        return "\n\n".join(filter(None, texts)).strip()
