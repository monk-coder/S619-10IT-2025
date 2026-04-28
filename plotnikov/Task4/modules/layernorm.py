import numpy as np

class LayerNorm:
    def __init__(self, d_model, eps=1e-5):
        self.eps = eps
        self.gamma = np.ones(d_model, dtype=np.float32)
        self.beta = np.zeros(d_model, dtype=np.float32)
        self.grad_gamma = np.zeros(d_model, dtype=np.float32)
        self.grad_beta = np.zeros(d_model, dtype=np.float32)

    def forward(self, x):
        self.x_shape = x.shape
        x = x.reshape(-1, x.shape[-1])
        self.mean = x.mean(axis=0)
        self.var = x.var(axis=0)
        self.x_norm = (x - self.mean) / np.sqrt(self.var + self.eps)
        out = self.gamma * self.x_norm + self.beta
        return out.reshape(self.x_shape)

    def backward(self, grad_output):
        grad_output = grad_output.reshape(-1, grad_output.shape[-1])
        N = grad_output.shape[0]
        self.grad_beta = grad_output.sum(axis=0)
        self.grad_gamma = (grad_output * self.x_norm).sum(axis=0)
        
        dx_norm = grad_output * self.gamma
        dvar = (dx_norm * (-0.5) * self.x_norm / (self.var + self.eps)).sum(axis=0)
        dmean = (-dx_norm / np.sqrt(self.var + self.eps)).sum(axis=0)
        
        dx = dx_norm / np.sqrt(self.var + self.eps) + dvar * 2 * (self.x_norm * np.sqrt(self.var + self.eps)) / N + dmean / N
        return dx.reshape(self.x_shape)

    def zero_grad(self):
        self.grad_gamma.fill(0)
        self.grad_beta.fill(0)