# utils.py
import numpy as np

def stable_softmax(x, axis=-1):
    """Численно стабильный softmax"""
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / (np.sum(exp_x, axis=axis, keepdims=True) + 1e-9)

def create_causal_mask(T, dtype=np.float32):
    """Создаёт causal mask размера (1, 1, T, T)"""
    mask = np.tril(np.ones((T, T), dtype=dtype))
    mask = mask.reshape(1, 1, T, T)
    mask = np.where(mask == 0, -1e9, 0)  # -inf заменяем на большое отрицательное
    return mask

def cross_entropy_loss(logits, targets, vocab_size):
    """Cross-entropy loss для next-token prediction"""
    # logits: (B, T, vocab_size), targets: (B, T)
    B, T, V = logits.shape
    logits_flat = logits.reshape(-1, V)
    targets_flat = targets.reshape(-1)
    
    # Stable log-softmax
    log_probs = logits_flat - np.max(logits_flat, axis=-1, keepdims=True)
    log_probs = log_probs - np.log(np.sum(np.exp(log_probs), axis=-1, keepdims=True) + 1e-9)
    
    # NLL loss
    loss = -np.mean(log_probs[np.arange(len(targets_flat)), targets_flat])
    return loss

def cross_entropy_backward(logits, targets, vocab_size):
    """Градиент cross-entropy loss"""
    B, T, V = logits.shape
    logits_flat = logits.reshape(-1, V)
    targets_flat = targets.reshape(-1)
    
    probs = stable_softmax(logits_flat, axis=-1)
    grad = probs.copy()
    grad[np.arange(len(targets_flat)), targets_flat] -= 1
    grad /= len(targets_flat)
    
    return grad.reshape(B, T, V)