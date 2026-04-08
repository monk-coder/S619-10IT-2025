class BPETokenizer:
    """Простой токенизатор на уровне символов"""

    def __init__(self):
        self.char_to_idx = {}
        self.idx_to_char = {}

    def train(self, text, vocab_size=None):
        # Get unique characters
        chars = sorted(list(set(text)))

        # Special tokens
        special_tokens = ['<PAD>', '<UNK>']

        # Build vocab
        all_tokens = special_tokens + chars
        if vocab_size:
            all_tokens = all_tokens[:vocab_size]

        self.char_to_idx = {ch: idx for idx, ch in enumerate(all_tokens)}
        self.idx_to_char = {idx: ch for ch, idx in self.char_to_idx.items()}

        print(f"Vocabulary size: {len(self.char_to_idx)}")
        return len(self.char_to_idx)

    def encode(self, text):
        """Convert text to token ids"""
        tokens = []
        for ch in text:
            if ch in self.char_to_idx:
                tokens.append(self.char_to_idx[ch])
            else:
                tokens.append(self.char_to_idx['<UNK>'])
        return tokens

    def decode(self, tokens):
        """Convert token ids back to text"""
        text = ''.join([self.idx_to_char.get(t, '<UNK>') for t in tokens])
        return text