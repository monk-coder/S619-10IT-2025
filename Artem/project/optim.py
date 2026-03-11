import numpy as np

class Adam:
    def __init__(self, model, lr=1e-4, beta1=0.9, beta2=0.999, eps=1e-8):
        self.model = model
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.t = 0
        self.m = {}
        self.v = {}
        
        for k in model.params:
            self.m[k] = np.zeros_like(model.params[k])
            self.v[k] = np.zeros_like(model.params[k])

    def step(self):
        self.t += 1
        for k in self.model.params:
            if k not in self.model.grads:
                continue
            
            g = self.model.grads[k]
            p = self.model.params[k]
            
            # Gradient clipping для стабильности
            g = np.clip(g, -0.5, 0.5)
            
            self.m[k] = self.beta1 * self.m[k] + (1 - self.beta1) * g
            self.v[k] = self.beta2 * self.v[k] + (1 - self.beta2) * (g ** 2)
            
            m_hat = self.m[k] / (1 - self.beta1 ** self.t)
            v_hat = self.v[k] / (1 - self.beta2 ** self.t)
            
            # Обновляем параметры НА МЕСТЕ
            p -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

    def zero_grad(self):
        self.model.zero_grad()