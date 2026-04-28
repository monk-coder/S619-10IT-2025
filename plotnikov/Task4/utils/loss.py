import numpy as np

def cross_entropy_loss(logits, targets):
    B, T, V = logits.shape
    logits_flat = logits.reshape(-1, V)
    logits_flat = logits_flat - logits_flat.max(axis=1, keepdims=True)
    exp_logits = np.exp(logits_flat)
    probs = exp_logits / (exp_logits.sum(axis=1, keepdims=True) + 1e-8)
    targets_flat = targets.reshape(-1)
    loss = -np.log(probs[np.arange(len(targets_flat)), targets_flat] + 1e-8).mean()
    grad = probs.copy()
    grad[np.arange(len(targets_flat)), targets_flat] -= 1
    grad = grad.reshape(B, T, V) / (B * T)
    return loss, grad