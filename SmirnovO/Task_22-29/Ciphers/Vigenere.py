class VigenereCipher:

    def __init__(self):
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz'
        self.alphabet_ru = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'

    def _prepare_key(self, key, length, use_russian=False):
        """Подготовка ключа нужной длины"""
        key = key.lower()
        if use_russian:
            key = self._translate_key_to_russian(key)

        key_repeated = (key * (length // len(key) + 1))[:length]
        return key_repeated

    def _translate_key_to_russian(self, key):
        translation = {
            'a': 'а', 'b': 'б', 'c': 'с', 'd': 'д', 'e': 'е',
            'f': 'ф', 'g': 'г', 'h': 'х', 'i': 'и', 'j': 'й',
            'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о',
            'p': 'п', 'q': 'к', 'r': 'р', 's': 'с', 't': 'т',
            'u': 'у', 'v': 'в', 'w': 'в', 'x': 'кс', 'y': 'ы', 'z': 'з'
        }

        result = []
        for char in key.lower():
            if char in translation:
                result.append(translation[char])
            else:
                result.append(char)
        return ''.join(result)

    def encrypt(self, text, key):
        result = []

        for i, char in enumerate(text):
            if char.lower() in self.alphabet:
                is_upper = char.isupper()
                text_idx = self.alphabet.index(char.lower())
                key_char = key[i % len(key)].lower()
                if key_char in self.alphabet:
                    key_idx = self.alphabet.index(key_char)
                else:
                    key_idx = ord(key_char) % len(self.alphabet)
                new_idx = (text_idx + key_idx) % len(self.alphabet)
                new_char = self.alphabet[new_idx]
                result.append(new_char.upper() if is_upper else new_char)

            elif char.lower() in self.alphabet_ru:
                is_upper = char.isupper()
                text_idx = self.alphabet_ru.index(char.lower())
                key_char = key[i % len(key)].lower()

                if key_char in self.alphabet:
                    key_char = self._translate_key_to_russian(key_char)[0]

                if key_char in self.alphabet_ru:
                    key_idx = self.alphabet_ru.index(key_char)
                else:
                    key_idx = ord(key_char) % len(self.alphabet_ru)

                new_idx = (text_idx + key_idx) % len(self.alphabet_ru)
                new_char = self.alphabet_ru[new_idx]
                result.append(new_char.upper() if is_upper else new_char)
            else:
                result.append(char)

        return ''.join(result)

    def decrypt(self, text, key):
        result = []

        for i, char in enumerate(text):
            if char.lower() in self.alphabet:
                is_upper = char.isupper()
                text_idx = self.alphabet.index(char.lower())
                key_char = key[i % len(key)].lower()
                if key_char in self.alphabet:
                    key_idx = self.alphabet.index(key_char)
                else:
                    key_idx = ord(key_char) % len(self.alphabet)
                new_idx = (text_idx - key_idx) % len(self.alphabet)
                new_char = self.alphabet[new_idx]
                result.append(new_char.upper() if is_upper else new_char)

            elif char.lower() in self.alphabet_ru:
                is_upper = char.isupper()
                text_idx = self.alphabet_ru.index(char.lower())
                key_char = key[i % len(key)].lower()

                if key_char in self.alphabet:
                    key_char = self._translate_key_to_russian(key_char)[0]

                if key_char in self.alphabet_ru:
                    key_idx = self.alphabet_ru.index(key_char)
                else:
                    key_idx = ord(key_char) % len(self.alphabet_ru)

                new_idx = (text_idx - key_idx) % len(self.alphabet_ru)
                new_char = self.alphabet_ru[new_idx]
                result.append(new_char.upper() if is_upper else new_char)
            else:
                result.append(char)

        return ''.join(result)


def main():
    print("=== Сравнение алгоритмов шифрования ===\n")

    original_text_en = "Hello World!"
    original_text_ru = "Привет Мир!"

    print("Английский текст:")
    print(f"Исходный текст: {original_text_en}\n")

    # Шифр Виженера для английского текста
    print("1. Шифр Виженера (английский текст):")
    vigenere = VigenereCipher()
    key = "secret"
    encrypted_vigenere_en = vigenere.encrypt(original_text_en, key)
    print(f"   Ключ: {key}")
    print(f"   Зашифровано: {encrypted_vigenere_en}")
    decrypted_vigenere_en = vigenere.decrypt(encrypted_vigenere_en, key)
    print(f"   Расшифровано: {decrypted_vigenere_en}")

    print("\n" + "=" * 50 + "\n")

    print("Русский текст:")
    print(f"Исходный текст: {original_text_ru}\n")

    # Шифр Виженера для русского текста (с русским ключом)
    print("2. Шифр Виженера (русский текст):")
    key_ru = "пароль"  # Используем русский ключ
    encrypted_vigenere_ru = vigenere.encrypt(original_text_ru, key_ru)
    print(f"   Ключ: {key_ru}")
    print(f"   Зашифровано: {encrypted_vigenere_ru}")
    decrypted_vigenere_ru = vigenere.decrypt(encrypted_vigenere_ru, key_ru)
    print(f"   Расшифровано: {decrypted_vigenere_ru}")

    # Альтернативно: английский ключ с русским текстом
    print("\n3. Шифр Виженера (русский текст с английским ключом):")
    key_en_for_ru = "secret"
    encrypted_mixed = vigenere.encrypt(original_text_ru, key_en_for_ru)
    print(f"   Ключ: {key_en_for_ru}")
    print(f"   Зашифровано: {encrypted_mixed}")
    decrypted_mixed = vigenere.decrypt(encrypted_mixed, key_en_for_ru)
    print(f"   Расшифровано: {decrypted_mixed}")


if __name__ == "__main__":
    main()