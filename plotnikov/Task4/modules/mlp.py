import numpy as np

def gelu(x):
    return 0.5 * x * (1 + np.tanh(np.sqrt(2/np.pi) * (x + 0.044715 * x**3)))

def gelu_backward(x, grad):
    tanh_val = np.tanh(np.sqrt(2/np.pi) * (x + 0.044715 * x**3))
    return grad * 0.5 * (1 + tanh_val + x * (1 - tanh_val**2) * np.sqrt(2/np.pi) * (1 + 3*0.044715*x**2))

class MLP:
    def __init__(self, d_model, d_ff, seed=42):
        rng = np.random.default_rng(seed)
        scale1 = np.sqrt(2.0 / d_model)
        scale2 = np.sqrt(2.0 / d_ff)
        self.W1 = rng.normal(0, scale1, (d_model, d_ff)).astype(np.float32)
        self.b1 = np.zeros(d_ff, dtype=np.float32)
        self.W2 = rng.normal(0, scale2, (d_ff, d_model)).astype(np.float32)
        self.b2 = np.zeros(d_model, dtype=np.float32)
        
        self.grad_W1 = np.zeros_like(self.W1)
        self.grad_b1 = np.zeros_like(self.b1)
        self.grad_W2 = np.zeros_like(self.W2)
        self.grad_b2 = np.zeros_like(self.b2)

    def forward(self, x):
        self.x = x
        self.z1 = x @ self.W1 + self.b1
        self.a1 = gelu(self.z1)
        self.z2 = self.a1 @ self.W2 + self.b2
        return self.z2

    def backward(self, grad_output):
        self.grad_W2 += self.a1.reshape(-1, self.a1.shape[-1]).T @ grad_output.reshape(-1, grad_output.shape[-1])
        self.grad_b2 += grad_output.sum(axis=(0, 1))
        da1 = grad_output @ self.W2.T
        
        dz1 = gelu_backward(self.z1, da1)
        
        x_flat = self.x.reshape(-1, self.x.shape[-1])
        self.grad_W1 += x_flat.T @ dz1.reshape(-1, dz1.shape[-1])
        self.grad_b1 += dz1.sum(axis=(0, 1))
        
        return dz1 @ self.W1.T

    def zero_grad(self):
        self.grad_W1.fill(0)
        self.grad_b1.fill(0)
        self.grad_W2.fill(0)
        self.grad_b2.fill(0)