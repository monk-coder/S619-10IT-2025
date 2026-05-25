import numpy as np


class Adam:
    def __init__(self, lr=1e-3, beta1=0.9, beta2=0.999, eps=1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = {}
        self.v = {}
        self.t = 0

    def update_param(self, param, grad, name):
        if name not in self.m:
            self.m[name] = np.zeros_like(param)
            self.v[name] = np.zeros_like(param)

        self.m[name] = self.beta1 * self.m[name] + (1 - self.beta1) * grad
        self.v[name] = self.beta2 * self.v[name] + (1 - self.beta2) * (grad ** 2)

        m_hat = self.m[name] / (1 - self.beta1 ** self.t)
        v_hat = self.v[name] / (1 - self.beta2 ** self.t)

        param -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

    def step(self, model):
        self.t += 1
        self.update_param(model.token_emb.weight, model.token_emb.dweight, 'wte')
        self.update_param(model.pos_emb.weight, model.pos_emb.dweight, 'wpe')
        self.update_param(model.lm_head, model.dlm_head, 'lm_head')

        self.update_param(model.ln_f.gamma, model.ln_f.dgamma, 'ln_f_g')
        self.update_param(model.ln_f.beta, model.ln_f.dbeta, 'ln_f_b')

        for i, block in enumerate(model.blocks):
            self.update_param(block.ln1.gamma, block.ln1.dgamma, f'b{i}_ln1_g')
            self.update_param(block.ln1.beta, block.ln1.dbeta, f'b{i}_ln1_b')
            self.update_param(block.ln2.gamma, block.ln2.dgamma, f'b{i}_ln2_g')
            self.update_param(block.ln2.beta, block.ln2.dbeta, f'b{i}_ln2_b')

            self.update_param(block.attn.W_q, block.attn.dW_q, f'b{i}_q')
            self.update_param(block.attn.W_k, block.attn.dW_k, f'b{i}_k')
            self.update_param(block.attn.W_v, block.attn.dW_v, f'b{i}_v')
            self.update_param(block.attn.W_o, block.attn.dW_o, f'b{i}_o')

            self.update_param(block.mlp.W1, block.mlp.dW1, f'b{i}_mlp1')
            self.update_param(block.mlp.b1, block.mlp.db1, f'b{i}_mlpb1')
            self.update_param(block.mlp.W2, block.mlp.dW2, f'b{i}_mlp2')
            self.update_param(block.mlp.b2, block.mlp.db2, f'b{i}_mlpb2')
