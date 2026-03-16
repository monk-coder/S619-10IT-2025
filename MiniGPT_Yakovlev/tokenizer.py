import json
from typing import List, Dict, Tuple


class BPETokenizer:
    
    def __init__(self) -> None:
        self.vocab: Dict[str, int] = {}
        self.merges: List[Tuple[str, str]] = []
        self._inv_vocab: Dict[int, str] = {}
        self.eos_token = "</s>"
        self.eos_token_id = None
    
    def _merge_tokens(self, tokens: List[str], pair: Tuple[str, str], replacement: str) -> List[str]:
        result = []
        i = 0
        while i < len(tokens):
            if i < len(tokens) - 1 and tokens[i] == pair[0] and tokens[i + 1] == pair[1]:
                result.append(replacement)
                i += 2
            else:
                result.append(tokens[i])
                i += 1
        return result
    
    def encode(self, text: str) -> List[int]:
        if not text:
            return []
        tokens = list(text)
        for pair in self.merges:
            new_token = ''.join(pair)
            tokens = self._merge_tokens(tokens, pair, new_token)
        ids = []
        for token in tokens:
            if token in self.vocab:
                ids.append(self.vocab[token])
            else:
                for char in token:
                    if char in self.vocab:
                        ids.append(self.vocab[char])
        return ids
    
    def decode(self, ids: List[int]) -> str:
        return ''.join(self._inv_vocab.get(idx, '') for idx in ids)
    
    @classmethod
    def load(cls, path: str) -> 'BPETokenizer':
        obj = cls()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        obj.vocab = data['vocab']
        obj.merges = [tuple(pair) for pair in data['merges']]
        obj.eos_token = data.get('eos_token', '</s>')
        obj.eos_token_id = data.get('eos_token_id', len(obj.vocab) - 1)
        obj._inv_vocab = {idx: token for token, idx in obj.vocab.items()}
        return obj
    
    def __len__(self) -> int:
        return len(self.vocab)
    
    def __repr__(self) -> str:
        return f"BPETokenizer(vocab_size={len(self.vocab)}, merges={len(self.merges)})"
