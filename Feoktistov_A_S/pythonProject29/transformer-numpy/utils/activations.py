import numpy as np

def gelu(x):
    """GELU активация"""
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

def gelu_derivative(x):
    """Производная GELU"""
    tanh_out = np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3))
    return 0.5 * (1 + tanh_out) + 0.5 * x * (1 - tanh_out**2) * np.sqrt(2 / np.pi) * (1 + 3 * 0.044715 * x**2)

def relu(x):
    return np.maximum(0, x)

def relu_derivative(x):
    return (x > 0).astype(float)