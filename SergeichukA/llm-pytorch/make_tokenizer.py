# make_tokenizer.py
import pickle
import sys
import os

# Подтягиваем ваш BPE-токенизатор из прошлой папки
sys.path.append(r"C:\Users\Администратор\Desktop\minigbt_numpy")
from tokenizer import BPETokenizer

data_path = "data.txt"
if not os.path.exists(data_path):
    print("❌ data.txt не найден в текущей папке!")
    sys.exit(1)

print("🔤 Обучение BPE токенизатора...")
with open(data_path, "r", encoding="utf-8") as f:
    text = f.read()

tokenizer = BPETokenizer(vocab_size=500)  # vocab_size должен совпадать с train.py
tokenizer.train(text)

with open("tokenizer.pkl", "wb") as f:
    pickle.dump(tokenizer, f)

print(f"✅ Сохранено: tokenizer.pkl | Vocab size: {tokenizer.vocab_len}")