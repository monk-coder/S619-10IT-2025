import numpy as np


class SGD:
    """Stochastic Gradient Descent with momentum"""

    def __init__(self, params, lr=0.01, momentum=0.9):
        self.params = params
        self.lr = lr
        self.momentum = momentum
        self.velocities = [np.zeros_like(p) for p in params]

    def step(self):
        for i, param in enumerate(self.params):
            if hasattr(param, 'dW'):
                grad = param.dW
                self.velocities[i] = self.momentum * self.velocities[i] - self.lr * grad
                param.W += self.velocities[i]

            if hasattr(param, 'db'):
                grad = param.db
                self.velocities[i] = self.momentum * self.velocities[i] - self.lr * grad
                param.b += self.velocities[i]

    def zero_grad(self):
        pass  # Gradients are computed and stored in each layer


class Adam:
    """Adam optimizer"""

    def __init__(self, params, lr=0.001, betas=(0.9, 0.999), eps=1e-8):
        self.params = params
        self.lr = lr
        self.beta1, self.beta2 = betas
        self.eps = eps
        self.m = [None] * len(params)
        self.v = [None] * len(params)
        self.t = 0

    def step(self):
        self.t += 1
        for i, param in enumerate(self.params):
            if hasattr(param, 'dW') and param.dW is not None:
                grad = param.dW
                if self.m[i] is None:
                    self.m[i] = np.zeros_like(grad)
                    self.v[i] = np.zeros_like(grad)

                self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad
                self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grad ** 2)

                m_hat = self.m[i] / (1 - self.beta1 ** self.t)
                v_hat = self.v[i] / (1 - self.beta2 ** self.t)

                param.W -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

            if hasattr(param, 'db') and param.db is not None:
                grad = param.db
                if self.m[i] is None:
                    self.m[i] = np.zeros_like(grad)
                    self.v[i] = np.zeros_like(grad)

                self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad
                self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grad ** 2)

                m_hat = self.m[i] / (1 - self.beta1 ** self.t)
                v_hat = self.v[i] / (1 - self.beta2 ** self.t)

                param.b -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

    def zero_grad(self):
        pass