import argparse
from gpt import sample

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--prompt', type=str, default="The future of")
    parser.add_argument('--max_new_tokens', type=int, default=None)
    parser.add_argument('--temperature', type=float, default=None)
    parser.add_argument('--top_k', type=int, default=None)
    parser.add_argument('--checkpoint', type=str, default=None)
    args = parser.parse_args()
    result = sample(args.prompt, args.max_new_tokens, args.temperature, args.top_k, args.checkpoint)
    print(f"\nPrompt: \"{args.prompt}\"\n{'-'*60}\n{result}\n{'-'*60}")
