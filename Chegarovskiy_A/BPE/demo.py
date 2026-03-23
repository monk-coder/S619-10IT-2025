"""
Демонстрация работы BPE токенизатора
"""

import argparse
from bpe import BPETokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='bpe_8000', help='файл модели')
    args = parser.parse_args()
    
    print("="*50)
    print("BPE TOKENIZER DEMO")
    print("="*50)
    
    tok = BPETokenizer().load(args.model)
    
    print(f"\nСловарь: {len(tok.vocab)} токенов")
    print(f"Слияний: {len(tok.merges)}")
    
    examples = [
        "Привет, мир!",
        "Как дела?",
        "Машинное обучение",
        "Python программирование",
        "12345"
    ]
    
    print("\n" + "-"*50)
    print("ПРИМЕРЫ:")
    print("-"*50)
    
    for text in examples:
        ids = tok.encode(text)
        decoded = tok.decode(ids)
        status = "✓" if decoded == text else "✗"
        
        print(f"\nТекст: {text}")
        print(f"Токены ({len(ids)}): {ids[:10]}{'...' if len(ids)>10 else ''}")
        print(f"Декод: {decoded} {status}")
    
    print("\n" + "-"*50)
    print("ПЕРВЫЕ 10 ТОКЕНОВ:")
    print("-"*50)
    
    sorted_vocab = sorted(tok.vocab.items(), key=lambda x: x[1])
    for token, idx in sorted_vocab[:10]:
        print(f"{idx:4d}: {repr(token)}")


if __name__ == '__main__':
    main()
