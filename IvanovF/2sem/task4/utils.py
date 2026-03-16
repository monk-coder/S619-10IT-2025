import numpy as np


def causal_mask(T: int) -> np.ndarray:
    """Causal mask: позиция i не видит j > i"""
    return np.triu(np.full((T, T), -np.inf, dtype=np.float32), k=1)


def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """Стабильный softmax"""
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / (np.sum(e, axis=axis, keepdims=True) + 1e-9)


def gelu(x: np.ndarray) -> np.ndarray:
    """GELU активация"""
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))


def gelu_backward(x: np.ndarray, grad: np.ndarray) -> np.ndarray:
    """Градиент GELU"""
    t = np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3))
    dg = 0.5 * (1 + t) + 0.5 * x * (1 - t**2) * np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x**2)
    return grad * dg


def cross_entropy_loss(logits: np.ndarray, targets: np.ndarray) -> tuple[float, np.ndarray]:
    """
    CE loss + probs для backward.
    logits: (B, T, V), targets: (B, T)
    Returns: loss, probs (B, T, V)
    """
    B, T, V = logits.shape
    
    # Stable softmax
    logits_flat = logits.reshape(-1, V)
    logits_flat = logits_flat - np.max(logits_flat, axis=-1, keepdims=True)
    exp = np.exp(logits_flat)
    probs_flat = exp / (np.sum(exp, axis=-1, keepdims=True) + 1e-9)
    
    # CE loss
    targets_flat = targets.reshape(-1)
    loss = -np.log(probs_flat[np.arange(len(targets_flat)), targets_flat] + 1e-9).mean()
    
    # Возвращаем probs правильной формы (B, T, V)
    probs = probs_flat.reshape(B, T, V)
    return float(loss), probs


def cross_entropy_backward(probs: np.ndarray, targets: np.ndarray) -> np.ndarray:
    """Градиент CE по logits. probs: (B, T, V), targets: (B, T)"""
    B, T, V = probs.shape
    g = probs.reshape(-1, V).copy()
    g[np.arange(B * T), targets.reshape(-1)] -= 1
    return g.reshape(B, T, V) / (B * T)


def init_weights(shape: tuple, std: float = 0.02) -> np.ndarray:
    """GPT-style init"""
    return np.random.randn(*shape).astype(np.float32) * std