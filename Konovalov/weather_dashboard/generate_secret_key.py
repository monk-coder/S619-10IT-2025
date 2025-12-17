#!/usr/bin/env python
"""
Генерация безопасного SECRET_KEY для Django
"""
import secrets
import string

def generate_secret_key(length=50):
    """Генерация случайного секретного ключа"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Убираем проблемные символы
    for char in ['\\', '"', "'", '`']:
        alphabet = alphabet.replace(char, '')
    
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == '__main__':
    secret_key = generate_secret_key()
    print(f"Сгенерированный SECRET_KEY: {secret_key}")
    print("\nДобавьте его в .env файл:")
    print(f"SECRET_KEY={secret_key}")