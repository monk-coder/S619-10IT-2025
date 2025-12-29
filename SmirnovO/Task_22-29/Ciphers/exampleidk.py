from Ceasar import CaesarCipher
from Vigenere import VigenereCipher
from XOR import XORCipher


def main():
    print("=== Сравнение алгоритмов шифрования ===\n")

    original_text = "Hello World! Привет Мир!"
    print(f"Исходный текст: {original_text}\n")

    # 1. Шифр Цезаря
    print("1. Шифр Цезаря (ROT13):")
    caesar = CaesarCipher(shift=13)
    encrypted_caesar = caesar.encrypt(original_text)
    print(f"   Зашифровано: {encrypted_caesar}")
    decrypted_caesar = caesar.decrypt(encrypted_caesar)
    print(f"   Расшифровано: {decrypted_caesar}")

    # 2. Шифр Виженера
    print("\n2. Шифр Виженера:")
    vigenere = VigenereCipher()
    key = "secret"
    encrypted_vigenere = vigenere.encrypt(original_text, key)
    print(f"   Ключ: {key}")
    print(f"   Зашифровано: {encrypted_vigenere}")
    decrypted_vigenere = vigenere.decrypt(encrypted_vigenere, key)
    print(f"   Расшифровано: {decrypted_vigenere}")

    # 3. XOR шифрование
    print("\n3. XOR шифрование:")
    xor_cipher = XORCipher(key="mysecretkey")
    encrypted_xor = xor_cipher.encrypt(original_text)
    print(f"   Зашифровано (сырые символы): {encrypted_xor}")
    encrypted_xor_hex = xor_cipher.encrypt_to_hex(original_text)
    print(f"   Зашифровано (hex): {encrypted_xor_hex}")
    decrypted_xor = xor_cipher.decrypt(encrypted_xor)
    print(f"   Расшифровано: {decrypted_xor}")

    # Сравнение характеристик
    print("\n" + "=" * 50)
    print("Сравнительная таблица:")
    print("-" * 50)
    print(f"{'Алгоритм':<20} {'Тип':<15} {'Сложность':<10}")
    print("-" * 50)
    print(f"{'Цезарь':<20} {'Симметричный':<15} {'O(n)':<10}")
    print(f"{'Виженер':<20} {'Симметричный':<15} {'O(n)':<10}")
    print(f"{'XOR':<20} {'Симметричный':<15} {'O(n)':<10}")
    print("-" * 50)

    # Тест безопасности
    print("\nТест на устойчивость к частотному анализу:")
    test_text = "аааабббвввггг" * 10
    caesar_test = caesar.encrypt(test_text)
    vigenere_test = vigenere.encrypt(test_text, "key")

    print(f"Цезарь (одинаковые символы): {caesar_test[:50]}...")
    print(f"Виженер (одинаковые символы): {vigenere_test[:50]}...")
    print("\nВывод: Виженер более устойчив к частотному анализу!")


if __name__ == "__main__":
    main()
