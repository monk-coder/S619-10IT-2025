import json
import os
import matplotlib.pyplot as plt
from collections import defaultdict

class BPETrainer:
    def __init__(self, vocab=None, merges=None):
        self.vocab = vocab if vocab is not None else []
        self.merges = merges if merges is not None else []
        self.token_to_id = {token: i for i, token in enumerate(self.vocab)} if vocab else {}

    def train(self, corpus, num_merges):
        tokenized_corpus = [list(text) for text in corpus]
        all_chars = sorted(set(char for text in corpus for char in text))
        vocab = all_chars.copy()
        merges = []

        for _ in range(num_merges):
            pair_freq = defaultdict(int)
            for doc in tokenized_corpus:
                for i in range(len(doc) - 1):
                    pair = (doc[i], doc[i + 1])
                    pair_freq[pair] += 1

            if not pair_freq:
                break

            most_freq_pair = max(pair_freq, key=pair_freq.get)
            a, b = most_freq_pair
            new_token = a + b

            for i in range(len(tokenized_corpus)):
                new_doc = []
                j = 0
                while j < len(tokenized_corpus[i]):
                    if j < len(tokenized_corpus[i]) - 1 and tokenized_corpus[i][j] == a and tokenized_corpus[i][j + 1] == b:
                        new_doc.append(new_token)
                        j += 2
                    else:
                        new_doc.append(tokenized_corpus[i][j])
                        j += 1
                tokenized_corpus[i] = new_doc

            merges.append((a, b))
            vocab.append(new_token)

        self.vocab = vocab
        self.merges = merges
        self.token_to_id = {token: i for i, token in enumerate(vocab)}

    def encode(self, text):
        tokens = list(text)
        for a, b in self.merges:
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] == a and tokens[i + 1] == b:
                    new_tokens.append(a + b)
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            tokens = new_tokens
        return [self.token_to_id[token] for token in tokens]

    def decode(self, ids):
        tokens = [self.vocab[id] for id in ids]
        return ''.join(tokens)

    def save(self, path):
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, 'vocab.txt'), 'w', encoding='utf-8') as f:
            for token in self.vocab:
                f.write(token + '\n')
        with open(os.path.join(path, 'merges.json'), 'w') as f:
            json.dump(self.merges, f)

    @classmethod
    def load(cls, path):
        with open(os.path.join(path, 'vocab.txt'), 'r', encoding='utf-8') as f:
            vocab = [line.strip() for line in f]
        with open(os.path.join(path, 'merges.json'), 'r') as f:
            merges = json.load(f)
        return cls(vocab=vocab, merges=merges)

def load_data(file_path, val_ratio=0.1, output_dir='.'):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    val_size = int(len(lines) * val_ratio)
    val = lines[:val_size]
    train = lines[val_size:]
    
    with open(os.path.join(output_dir, 'train.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(train))
    with open(os.path.join(output_dir, 'val.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(val))
    
    return train, val

def compute_metrics(trainer, val_corpus):
    vocab_size = len(trainer.vocab)
    total_length = 0
    lengths = []
    
    for text in val_corpus:
        ids = trainer.encode(text)
        length = len(ids)
        total_length += length
        lengths.append(length)
    
    avg_length = total_length / len(val_corpus)
    lengths.sort()
    threshold_idx = int(len(lengths) * 0.99)
    threshold = lengths[threshold_idx]
    share_long = sum(1 for l in lengths if l >= threshold) / len(lengths)
    
    return vocab_size, avg_length, share_long

if __name__ == "__main__":
    # Data preparation
    train_corpus, val_corpus = load_data('data.txt', val_ratio=0.1, output_dir='BPE')
    
    # Experiment with different num_merges
    num_merges_list = [0, 2000, 8000]
    results = []
    
    for num_merges in num_merges_list:
        trainer = BPETrainer()
        trainer.train(train_corpus, num_merges)
        vocab_size, avg_length, share_long = compute_metrics(trainer, val_corpus)
        results.append((num_merges, vocab_size, avg_length, share_long))
        trainer.save(f'BPE/BPE_{num_merges}')
    
    # Print results
    for res in results:
        print(f"num_merges={res[0]}, vocab_size={res[1]}, avg_length={res[2]:.2f}, share_long={res[3]:.4f}")
    
    # Plot results
    num_merges = [res[0] for res in results]
    avg_lengths = [res[2] for res in results]
    
    plt.figure(figsize=(10, 6))
    plt.plot(num_merges, avg_lengths, marker='o', linestyle='-', color='b')
    plt.title('Effect of BPE Merges on Average Token Sequence Length')
    plt.xlabel('Number of Merges')
    plt.ylabel('Average Token Length (on Validation Set)')
    plt.grid(True)
    plt.savefig('BPE/bpe_experiment.png')
    print("Experiment results saved to 'BPE/bpe_experiment.png'")