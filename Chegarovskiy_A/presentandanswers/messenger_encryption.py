# messenger_encryption.py
# Реализация двух типов шифрования для мессенджеров

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os
import base64

def print_step(step_name):
    """Функция для красивого вывода шагов"""
    print(f"\n{'='*50}")
    print(f"ШАГ: {step_name}")
    print(f"{'='*50}")

# ============================================================================
# ПОДХОД 1: СИММЕТРИЧНОЕ ШИФРОВАНИЕ (AES)
# ============================================================================
print_step("1. СИММЕТРИЧНОЕ ШИФРОВАНИЕ (AES)")

# Исходное сообщение
original_message = "Секретная встреча в 18:00 у фонтана".encode('utf-8')
print(f"Исходное сообщение: {original_message.decode('utf-8')}")

# 1.1. Генерация случайного ключа AES (256 бит)
# В реальном мессенджере этот ключ должен храниться в секрете у обоих участников
aes_key = os.urandom(32)  # 32 байта = 256 бит
print(f"\nКлюч AES (256 бит): {base64.b64encode(aes_key).decode('utf-8')}")

# 1.2. Шифрование сообщения
# AES работает с блоками по 16 байт, поэтому нужно дополнить сообщение
padder = padding.PKCS7(128).padder()
padded_data = padder.update(original_message) + padder.finalize()

# Создаем случайный вектор инициализации (IV) для режима CBC
iv = os.urandom(16)

# Создаем шифр и шифруем данные
cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
encryptor = cipher.encryptor()
encrypted_message = encryptor.update(padded_data) + encryptor.finalize()

print(f"Вектор инициализации (IV): {base64.b64encode(iv).decode('utf-8')}")
print(f"Зашифрованное сообщение (AES-CBC): {base64.b64encode(encrypted_message).decode('utf-8')}")

# 1.3. Расшифровка сообщения
cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
decryptor = cipher.decryptor()
decrypted_padded = decryptor.update(encrypted_message) + decryptor.finalize()

# Убираем дополнение
unpadder = padding.PKCS7(128).unpadder()
decrypted_message = unpadder.update(decrypted_padded) + unpadder.finalize()

print(f"Расшифрованное сообщение: {decrypted_message.decode('utf-8')}")

# Проверка
if decrypted_message == original_message:
    print("✓ AES шифрование/расшифровка работает корректно!")
else:
    print("✗ Ошибка в AES шифровании!")

# ============================================================================
# ПОДХОД 2: АСИММЕТРИЧНОЕ ШИФРОВАНИЕ (RSA)
# ============================================================================
print_step("2. АСИММЕТРИЧНОЕ ШИФРОВАНИЕ (RSA)")

# 2.1. Генерация пары ключей RSA
# В реальности: приватный ключ хранится в секрете, публичный - можно раздавать всем
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
public_key = private_key.public_key()

print("Сгенерирована пара ключей RSA (2048 бит):")
print(f"Приватный ключ (секретный): ...хранится у получателя...")
print(f"Публичный ключ (открытый): ...можно отправлять всем...")

# 2.2. Шифрование сообщения публичным ключом
# Важно: RSA может шифровать только небольшие данные (меньше размера ключа)
# Поэтому шифруем короткое сообщение
short_secret = "Ключ от сейфа: 12345".encode('utf-8')
print(f"\nСекрет для шифрования: {short_secret.decode('utf-8')}")

encrypted_secret = public_key.encrypt(
    short_secret,
    asym_padding.OAEP(
        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

print(f"Зашифрованный секрет (RSA-OAEP): {base64.b64encode(encrypted_secret).decode('utf-8')}")

# 2.3. Расшифровка приватным ключом
decrypted_secret = private_key.decrypt(
    encrypted_secret,
    asym_padding.OAEP(
        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

print(f"Расшифрованный секрет: {decrypted_secret.decode('utf-8')}")

if decrypted_secret == short_secret:
    print("✓ RSA шифрование/расшифровка работает корректно!")
else:
    print("✗ Ошибка в RSA шифровании!")

# ============================================================================
# ГИБРИДНАЯ СХЕМА (КАК В РЕАЛЬНЫХ МЕССЕНДЖЕРАХ)
# ============================================================================
print_step("3. ГИБРИДНАЯ СХЕМА (AES + RSA)")

print("РЕАЛЬНЫЙ СЦЕНАРИЙ МЕССЕНДЖЕРА:")
print("1. Алиса хочет отправить сообщение Бобу")
print("2. У Боба есть пара ключей RSA (публичный и приватный)")
print("3. Алиса генерирует случайный ключ AES для этого диалога")
print("4. Алиса шифрует ключ AES публичным ключом Боба (RSA)")
print("5. Алиса шифрует сообщение ключом AES")
print("6. Алиса отправляет Бобу: [зашифрованный ключ AES] + [зашифрованное сообщение]")
print("7. Боб расшифровывает ключ AES своим приватным ключом RSA")
print("8. Боб расшифровывает сообщение ключом AES")

# Имитация этого процесса:
print("\n--- Имитация процесса ---")

# У Боба есть ключи RSA (уже сгенерированы выше)
bob_private_key = private_key
bob_public_key = public_key

# Алиса генерирует ключ для сессии (сессионный ключ AES)
session_key = os.urandom(32)  # 256-битный ключ AES
print(f"\n1. Алиса генерирует сессионный ключ AES: {base64.b64encode(session_key).decode('utf-8')}")

# Сообщение Алисы
alice_message = "Завтра в 10:00, не опаздывай!".encode('utf-8')
print(f"2. Сообщение Алисы: {alice_message.decode('utf-8')}")

# Алиса шифрует сессионный ключ публичным ключом Боба (RSA)
encrypted_session_key = bob_public_key.encrypt(
    session_key,
    asym_padding.OAEP(
        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print(f"3. Алиса шифрует сессионный ключ RSA (публичным ключом Боба)")

# Алиса шифрует сообщение сессионным ключом AES
# (упрощенная версия без padding/IV для наглядности)
cipher = Cipher(algorithms.AES(session_key), modes.ECB(), backend=default_backend())
encryptor = cipher.encryptor()

# Дополняем сообщение до размера блока
padder = padding.PKCS7(128).padder()
padded_msg = padder.update(alice_message) + padder.finalize()

encrypted_msg = encryptor.update(padded_msg) + encryptor.finalize()
print(f"4. Алиса шифрует сообщение AES (сессионным ключом)")

# Алиса отправляет Бобу зашифрованный ключ и сообщение
print(f"5. Алиса отправляет Бобу 2 части данных:")
print(f"   Часть 1 (зашифрованный ключ): {base64.b64encode(encrypted_session_key).decode('utf-8')[:50]}...")
print(f"   Часть 2 (зашифрованное сообщение): {base64.b64encode(encrypted_msg).decode('utf-8')[:50]}...")

# Боб получает и расшифровывает
print(f"\n6. Боб получает данные от Алисы")

# Боб расшифровывает сессионный ключ своим приватным ключом RSA
decrypted_session_key = bob_private_key.decrypt(
    encrypted_session_key,
    asym_padding.OAEP(
        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print(f"7. Боб расшифровывает сессионный ключ своим приватным ключом RSA")
print(f"   Полученный ключ: {base64.b64encode(decrypted_session_key).decode('utf-8')}")

# Боб расшифровывает сообщение сессионным ключом AES
cipher = Cipher(algorithms.AES(decrypted_session_key), modes.ECB(), backend=default_backend())
decryptor = cipher.decryptor()
decrypted_padded = decryptor.update(encrypted_msg) + decryptor.finalize()

unpadder = padding.PKCS7(128).unpadder()
decrypted_message = unpadder.update(decrypted_padded) + unpadder.finalize()

print(f"8. Боб расшифровывает сообщение ключом AES")
print(f"   Расшифрованное сообщение: {decrypted_message.decode('utf-8')}")

if decrypted_message == alice_message:
    print("\n✓ ГИБРИДНАЯ СХЕМА РАБОТАЕТ! Так работают современные мессенджеры.")
else:
    print("\n✗ Ошибка в гибридной схеме!")

# ============================================================================
# СРАВНЕНИЕ ПОДХОДОВ
# ============================================================================
print_step("СРАВНЕНИЕ ПОДХОДОВ")

print("СИММЕТРИЧНОЕ (AES):")
print("  + Очень быстрое")
print("  + Подходит для больших данных")
print("  - Проблема: как безопасно передать ключ собеседнику?")
print("  Пример: Один ключ для шифрования/расшифровки всего чата")

print("\nАСИММЕТРИЧНОЕ (RSA):")
print("  + Решает проблему передачи ключа (публичный ключ можно не скрывать)")
print("  + Идеально для начального обмена секретами")
print("  - Медленное, требует много вычислений")
print("  - Может шифровать только небольшие данные (< 256 байт для 2048-битного ключа)")
print("  Пример: Отправка ключа AES, цифровые подписи")

print("\nГИБРИДНАЯ СХЕМА (AES + RSA):")
print("  + Объединяет преимущества обоих методов")
print("  + Быстрое шифрование сообщений (AES)")
print("  + Безопасная передача ключа (RSA)")
print("  + Используется в Signal Protocol, WhatsApp, Telegram Secret Chats")
print("  Пример: 1) RSA передаёт ключ AES, 2) AES шифрует весь дальнейший диалог")

print("\n" + "="*50)
print("ВЫВОД: Современные мессенджеры используют ГИБРИДНУЮ СХЕМУ")
print("RSA для установки безопасного соединения, AES для быстрого обмена сообщениями")
print("="*50)
