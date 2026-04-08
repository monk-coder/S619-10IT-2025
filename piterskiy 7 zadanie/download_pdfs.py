import os
import requests

DOCS_DIR = "docs"
os.makedirs(DOCS_DIR, exist_ok=True)

PDFS = {
    "attention_transformers.pdf": "https://arxiv.org/pdf/1706.03762.pdf",
    "stanford_ml_notes.pdf": "https://cs229.stanford.edu/notes2022fall/main_notes.pdf",
    "cnn_survey.pdf": "https://arxiv.org/pdf/2008.08695.pdf",
    "regularization_dropout.pdf": "https://arxiv.org/pdf/1908.08571.pdf",
    "ml_metrics.pdf": "https://arxiv.org/pdf/2006.14113.pdf",
}

print(f"📥 Скачиваю {len(PDFS)} файлов в папку '{DOCS_DIR}'...")

for filename, url in PDFS.items():
    filepath = os.path.join(DOCS_DIR, filename)
    if os.path.exists(filepath):
        print(f"✅ Уже есть: {filename}")
        continue
    try:
        print(f"⏳ {filename}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"✅ Готово: {filename}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("\n🎉 PDF загружены в docs/")
