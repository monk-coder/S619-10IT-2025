import argparse
from bpe_tokenizer import BPETokenizer
from utils import load_data, split_corpus


def main():

    print("START")

    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, required=True)
    parser.add_argument("--merges", type=int, default=2000)
    parser.add_argument("--save_path", type=str, default="bpe_model.json")

    args = parser.parse_args()

    lines = load_data(args.data)
    train, val = split_corpus(lines)

    tokenizer = BPETokenizer()
    tokenizer.train(train, num_merges=args.merges)
    tokenizer.save(args.save_path)

    print("Training complete.")
    print("Vocab size:", len(tokenizer.vocab))


if __name__ == "__main__":
    main()
