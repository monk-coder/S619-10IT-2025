import os
import sys
import time
import argparse
import torch
import numpy as np

_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_DIR, "..", "task4"))
sys.path.insert(0, os.path.join(_DIR, "..", "task3"))
sys.path.insert(0, _DIR)  # task5 идёт последним => перекрывает task4

from model import TransformerLM  # task5 pytorch model


def bench_torch(device, batch_size, T, vocab_size, d_model, n_head, n_layer, n_steps=50):
    model = TransformerLM(vocab_size, d_model, n_head, n_layer, T, dropout=0.0).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)

    x = torch.randint(0, vocab_size, (batch_size, T), device=device)
    y = torch.randint(0, vocab_size, (batch_size, T), device=device)

    if "cuda" in str(device):
        torch.cuda.synchronize()

    t0 = time.time()
    for _ in range(n_steps):
        _, loss = model(x, y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)

    if "cuda" in str(device):
        torch.cuda.synchronize()

    return n_steps / (time.time() - t0)


def bench_numpy(batch_size, T, vocab_size, d_model, n_head, n_layer, n_steps=10):
    import importlib.util
    task4_model = os.path.join(_DIR, "..", "task4", "model.py")
    try:
        spec = importlib.util.spec_from_file_location("numpy_model", task4_model)
        nm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(nm)

        model = nm.TransformerLM(vocab_size, d_model, n_head, n_layer, T)
        opt = nm.AdamOptimizer(model.params(), lr=3e-4)
        rng = np.random.RandomState(0)

        x = rng.randint(0, vocab_size, (batch_size, T)).astype(np.int32)
        y = rng.randint(0, vocab_size, (batch_size, T)).astype(np.int32)

        t0 = time.time()
        for _ in range(n_steps):
            logits = model.forward(x)
            loss, dlogits = nm.loss_fn(logits, y)
            model.zero_grad()
            model.backward(dlogits)
            opt.step()
        return n_steps / (time.time() - t0)
    except Exception as e:
        print(f"  numpy benchmark недоступен: {e}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--d_model", type=int, default=128)
    parser.add_argument("--n_head", type=int, default=4)
    parser.add_argument("--n_layer", type=int, default=2)
    parser.add_argument("--T", type=int, default=64)
    parser.add_argument("--vocab_size", type=int, default=2000)
    args = parser.parse_args()

    V = args.vocab_size
    cfg = dict(T=args.T, vocab_size=V, d_model=args.d_model, n_head=args.n_head, n_layer=args.n_layer)

    print("=" * 55)
    print("  Benchmark: numpy vs PyTorch CPU vs PyTorch GPU")
    print("=" * 55)

    print("\n1. numpy (task4)")
    numpy_ips = bench_numpy(16, **cfg, n_steps=10)
    if numpy_ips:
        print(f"   {numpy_ips:.2f} it/s")

    print("\n2. PyTorch CPU")
    cpu_ips = bench_torch("cpu", 16, **cfg, n_steps=30)
    print(f"   {cpu_ips:.2f} it/s")

    gpu_ips = None
    if torch.cuda.is_available():
        print("\n3. PyTorch CUDA")
        gpu_ips = bench_torch("cuda", 16, **cfg, n_steps=100)
        print(f"   {gpu_ips:.2f} it/s")
    else:
        print("\n3. PyTorch CUDA — GPU недоступен")

    print("\n" + "=" * 55)
    if numpy_ips:
        print(f"  PyTorch CPU vs numpy:  {cpu_ips / numpy_ips:.1f}x")
        if gpu_ips:
            print(f"  PyTorch GPU vs numpy:  {gpu_ips / numpy_ips:.1f}x")
            print(f"  PyTorch GPU vs CPU:    {gpu_ips / cpu_ips:.1f}x")

    print("\nBatch size scaling (PyTorch CPU):")
    print(f"{'batch_size':>12} | {'it/s':>8}")
    print("-" * 24)
    for bs in [16, 64, 128]:
        ips = bench_torch("cpu", bs, **cfg, n_steps=20)
        print(f"{bs:>12} | {ips:>8.2f}")


if __name__ == "__main__":
    main()