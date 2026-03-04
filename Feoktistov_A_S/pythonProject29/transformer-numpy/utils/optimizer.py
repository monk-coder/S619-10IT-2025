import numpy as np


class Adam:
    def __init__(self, params, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        self.params = params  # список кортежей (param, grad)
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps

        self.t = 0
        self.m = []  # моменты первого порядка
        self.v = []  # моменты второго порядка

        for param, _ in params:
            self.m.append(np.zeros_like(param))
            self.v.append(np.zeros_like(param))

    def step(self):
        self.t += 1

        for i, (param, grad) in enumerate(self.params):
            # Обновляем моменты
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * grad
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * (grad ** 2)

            # Коррекция смещения
            m_hat = self.m[i] / (1 - self.beta1 ** self.t)
            v_hat = self.v[i] / (1 - self.beta2 ** self.t)

            # Обновляем параметры
            param -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

    def zero_grad(self):
        for _, grad in self.params:
            grad.fill(0)