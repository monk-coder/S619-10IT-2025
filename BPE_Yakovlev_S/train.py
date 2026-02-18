import argparse
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
from tqdm import tqdm

from bpe_tokenizer import BPETokenizer


def setup_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train BPE tokenizer on text corpus",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--data',
        type=str,
        default='data.txt',
        help='Path to input text corpus (UTF-8 encoded)'
    )
    
    parser.add_argument(
        '--merges',
        type=int,
        default=2000,
        help='Number of BPE merge operations'
    )
    
    parser.add_argument(
        '--val-split',
        type=float,
        default=0.1,
        help='Fraction of data for validation (0.0 to 1.0)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='tokenizer.json',
        help='Path to save trained tokenizer'
    )
    
    parser.add_argument(
        '--experiment',
        action='store_true',
        help='Run experiment with multiple merge values'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Disable progress bars'
    )
    
    return parser


def validate_file(path: str) -> Path:
    file_path = Path(path)
    
    if not file_path.exists():
        print(f"\n❌ Error: File not found: {file_path.absolute()}")
        print("\n💡 Make sure 'data.txt' is in the same directory as this script")
        sys.exit(1)
    
    if file_path.stat().st_size == 0:
        print(f"\n❌ Error: File is empty: {file_path}")
        sys.exit(1)
    
    return file_path


def evaluate_tokenizer(tokenizer: BPETokenizer, lines: List[str], desc: str = "Evaluating") -> Dict:
    lengths = []
    
    for line in tqdm(lines, desc=desc, unit="line", ncols=80):
        # Encode and decode
        ids = tokenizer.encode(line)
        decoded = tokenizer.decode(ids)
        
        if decoded != line:
            print(f"\n\n❌ Reversibility check failed!")
            print(f"   Original: {repr(line)}")
            print(f"   Decoded:  {repr(decoded)}")
            print(f"   IDs: {ids}")
            raise AssertionError(f"decode(encode(x)) != x")
        
        lengths.append(len(ids))
    
    lengths_arr = np.array(lengths)
    
    return {
        'vocab_size': len(tokenizer.vocab),
        'avg_length': float(lengths_arr.mean()),
        'median_length': float(np.median(lengths_arr)),
        'max_length': int(lengths_arr.max()),
        'p99_length': float(np.percentile(lengths_arr, 99)),
        'total_samples': len(lines)
    }


def print_metrics(metrics: Dict, title: str = "Metrics") -> None:
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")
    print(f"  • Vocabulary size:     {metrics['vocab_size']:>8,}")
    print(f"  • Average length:      {metrics['avg_length']:>8.2f} tokens")
    print(f"  • Median length:       {metrics['median_length']:>8.2f} tokens")
    print(f"  • 99th percentile:     {metrics['p99_length']:>8.1f} tokens")
    print(f"  • Maximum length:      {metrics['max_length']:>8} tokens")
    print(f"  • Total samples:       {metrics['total_samples']:>8}")


def run_experiment(
    data_path: str,
    merge_values: List[int],
    val_split: float,
    output_base: str = "tokenizer"
) -> List[Dict]:
    print(f"\n{'='*60}")
    print("🔬 EXPERIMENT: Effect of num_merges")
    print(f"{'='*60}")
    
    results = []
    
    for i, num_merges in enumerate(merge_values, 1):
        print(f"\n[{i}/{len(merge_values)}] Training with num_merges={num_merges:,}")
        
        tokenizer = BPETokenizer()
        tokenizer.train(
            data_path,
            num_merges=num_merges,
            val_split=val_split,
            show_progress=False
        )
        
        metrics = evaluate_tokenizer(
            tokenizer,
            tokenizer.val_lines,
            desc=f"  Evaluating"
        )
        
        output_path = f"{output_base}_merges{num_merges}.json"
        tokenizer.save(output_path)
        
        results.append({
            'num_merges': num_merges,
            **metrics,
            'output_path': output_path
        })
        
        print(f"  → Saved to: {output_path}")
    
    return results


def demonstrate_encoding(tokenizer: BPETokenizer) -> None:
    print(f"\n{'='*60}")
    print("🧪 DEMONSTRATION")
    print(f"{'='*60}")
    
    # Select example text
    if tokenizer.val_lines:
        example = tokenizer.val_lines[0]
    else:
        example = "Привет, мир! Это тест BPE токенизатора."
    
    print(f"\nInput text:")
    print(f"  {repr(example)}")
    
    ids = tokenizer.encode(example)
    print(f"\nToken IDs ({len(ids)} tokens):")
    print(f"  {ids}")
    
    tokens = [tokenizer._inv_vocab[i] for i in ids]
    print(f"\nTokens:")
    print(f"  {tokens}")
    
    decoded = tokenizer.decode(ids)
    print(f"\nDecoded text:")
    print(f"  {repr(decoded)}")
    
    status = "✅ SUCCESS" if decoded == example else "❌ FAILED"
    print(f"\nReversibility: {status}")


def main() -> None:
    # Parse arguments
    parser = setup_argparser()
    args = parser.parse_args()
    
    data_path = validate_file(args.data)
    
    print(f"\n{'='*60}")
    print("🚀 BPE TOKENIZER TRAINING")
    print(f"{'='*60}")
    print(f"📁 Corpus:      {data_path.absolute()}")
    print(f"🔄 Merges:      {args.merges:,}")
    print(f"📊 Val split:   {args.val_split:.0%}")
    print(f"💾 Output:      {args.output}")
    
    print(f"\n{'─'*60}")
    print("📚 TRAINING")
    print(f"{'─'*60}")
    
    tokenizer = BPETokenizer()
    tokenizer.train(
        str(data_path),
        num_merges=args.merges,
        val_split=args.val_split,
        show_progress=not args.quiet
    )
    
    print(f"\n✅ Training complete!")
    print(f"   Vocabulary size: {len(tokenizer.vocab):,}")
    print(f"   Merge operations: {len(tokenizer.merges):,}")
    
    tokenizer.save(args.output)
    print(f"   Saved to: {Path(args.output).absolute()}")
    
    print(f"\n{'─'*60}")
    print("🔍 VALIDATION")
    print(f"{'─'*60}")
    
    metrics = evaluate_tokenizer(
        tokenizer,
        tokenizer.val_lines,
        desc="Validating"
    )
    
    print_metrics(metrics, "Validation Results")
    
    demonstrate_encoding(tokenizer)
    
    if args.experiment:
        print(f"\n{'─'*60}")
        print("🔬 EXPERIMENT MODE")
        print(f"{'─'*60}")
        
        merge_values = [0, 500, 2000, 5000]
        experiment_results = run_experiment(
            str(data_path),
            merge_values,
            args.val_split
        )
        
        print(f"\n{'='*60}")
        print("📈 EXPERIMENT SUMMARY")
        print(f"{'='*60}")
        print(f"{'Merges':<12} {'Vocab Size':<15} {'Avg Length':<15}")
        print(f"{'─'*60}")
        for res in experiment_results:
            print(f"{res['num_merges']:<12,} {res['vocab_size']:<15,} {res['avg_length']:<15.2f}")
    
    print(f"\n{'='*60}")
    print("✅ ALL DONE!")
    print(f"{'='*60}")
    print("\n💡 Quick commands:")
    print(f"   python {sys.argv[0]} --merges 1000")
    print(f"   python {sys.argv[0]} --experiment")


if __name__ == '__main__':
    main()
