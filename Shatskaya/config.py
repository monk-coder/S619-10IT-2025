from dataclasses import dataclass

@dataclass
class Config:
    vocab_size: int = 50257
    d_model: int = 256
    n_layer: int = 4
    n_head: int = 8
    block_size: int = 256
    batch_size: int = 32
    learning_rate: float = 3e-4
    max_iters: int = 5000
    eval_interval: int = 200
    eval_iters: int = 100
    warmup_steps: int = 500
    grad_clip: float = 1.0
    weight_decay: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.95
    device: str = "cuda" if import("torch").cuda.is_available() else "cpu"