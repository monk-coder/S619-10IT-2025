class CaesarCipher:

    def __init__(self, shift=13):
        self.shift = shift
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz'
        self.alphabet_ru = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'

    def encrypt(self, text):
        result = []
        for char in text:
            if char.lower() in self.alphabet:
                is_upper = char.isupper()
                idx = self.alphabet.index(char.lower())
                new_idx = (idx + self.shift) % len(self.alphabet)
                new_char = self.alphabet[new_idx]
                result.append(new_char.upper() if is_upper else new_char)
            elif char.lower() in self.alphabet_ru:
                is_upper = char.isupper()
                idx = self.alphabet_ru.index(char.lower())
                new_idx = (idx + self.shift) % len(self.alphabet_ru)
                new_char = self.alphabet_ru[new_idx]
                result.append(new_char.upper() if is_upper else new_char)
            else:
                result.append(char)
        return ''.join(result)

    def decrypt(self, text):
        self.shift = -self.shift
        decrypted = self.encrypt(text)
        self.shift = -self.shift
        return decrypted

    def brute_force(self, text):
        results = []
        original_shift = self.shift
        for shift in range(1, len(self.alphabet)):
            self.shift = shift
            results.append((shift, self.decrypt(text)))
        self.shift = original_shift
        return results