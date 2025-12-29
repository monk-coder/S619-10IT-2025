class XORCipher:

    def __init__(self, key):
        self.key = key

    def encrypt(self, text):
        result = []
        key_bytes = self.key.encode('utf-8')
        key_length = len(key_bytes)

        for i, char in enumerate(text):
            key_byte = key_bytes[i % key_length]
            encrypted_byte = ord(char) ^ key_byte
            result.append(chr(encrypted_byte))

        return ''.join(result)

    def decrypt(self, text):
        return self.encrypt(text)

    def encrypt_to_hex(self, text):
        encrypted = self.encrypt(text)
        return ''.join(f'{ord(c):02x}' for c in encrypted)

    def decrypt_from_hex(self, hex_string):
        text = ''.join(chr(int(hex_string[i:i + 2], 16))
                       for i in range(0, len(hex_string), 2))
        return self.decrypt(text)