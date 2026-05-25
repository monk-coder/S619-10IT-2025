import numpy as np


def gelu(x):
    return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * np.power(x, 3))))


def gelu_prime(x):
    tanh_arg = np.sqrt(2.0 / np.pi) * (x + 0.044715 * np.power(x, 3))
    t = np.tanh(tanh_arg)
    dtanh = 1.0 - t ** 2
    dtanh_arg = np.sqrt(2.0 / np.pi) * (1.0 + 3 * 0.044715 * x ** 2)
    return 0.5 * (1.0 + t) + 0.5 * x * dtanh * dtanh_arg


class LayerNorm:
    def __init__(self, d_model, eps=1e-5):
        self.gamma = np.ones(d_model, dtype=np.float32)
        self.beta = np.zeros(d_model, dtype=np.float32)
        self.eps = eps

        self.dgamma = None
        self.dbeta = None

    def forward(self, x):
        self.x = x
        self.mean = np.mean(x, axis=-1, keepdims=True)
        self.var = np.var(x, axis=-1, keepdims=True)
        self.x_hat = (x - self.mean) / np.sqrt(self.var + self.eps)
        return self.gamma * self.x_hat + self.beta

    def backward(self, dout):
        N = dout.shape[-1]
        self.dgamma = np.sum(dout * self.x_hat, axis=(0, 1))
        self.dbeta = np.sum(dout, axis=(0, 1))

        dx_hat = dout * self.gamma
        ivar = 1.0 / np.sqrt(self.var + self.eps)

        dvar = np.sum(dx_hat * (self.x - self.mean) * -0.5 * (ivar ** 3), axis=-1, keepdims=True)
        dmean = np.sum(dx_hat * -ivar, axis=-1, keepdims=True) + dvar * np.mean(-2.0 * (self.x - self.mean), axis=-1,
                                                                                keepdims=True)

        dx = dx_hat * ivar + dvar * 2.0 * (self.x - self.mean) / N + dmean / N
        return dx


class MultiHeadAttention:
    def __init__(self, d_model, n_head):
        self.d_model = d_model
        self.n_head = n_head
        self.d_head = d_model // n_head

        limit = np.sqrt(6.0 / (d_model + d_model))
        self.W_q = np.random.uniform(-limit, limit, (d_model, d_model)).astype(np.float32)
        self.W_k = np.random.uniform(-limit, limit, (d_model, d_model)).astype(np.float32)
        self.W_v = np.random.uniform(-limit, limit, (d_model, d_model)).astype(np.float32)
        self.W_o = np.random.uniform(-limit, limit, (d_model, d_model)).astype(np.float32)

        self.dW_q, self.dW_k, self.dW_v, self.dW_o = None, None, None, None

    def forward(self, x):
        self.x = x
        B, T, C = x.shape
        H, D = self.n_head, self.d_head

        self.q = x.dot(self.W_q).reshape(B, T, H, D).transpose(0, 2, 1, 3)
        self.k = x.dot(self.W_k).reshape(B, T, H, D).transpose(0, 2, 1, 3)
        self.v = x.dot(self.W_v).reshape(B, T, H, D).transpose(0, 2, 1, 3)

        scores = np.matmul(self.q, self.k.transpose(0, 1, 3, 2)) / np.sqrt(D)

        mask = np.tril(np.ones((T, T))) == 0
        self.mask_indices = mask
        scores[:, :, mask] = -1e9

        max_scores = np.max(scores, axis=-1, keepdims=True)
        exp_scores = np.exp(scores - max_scores)
        exp_scores[:, :, mask] = 0.0
        self.probs = exp_scores / (np.sum(exp_scores, axis=-1, keepdims=True) + 1e-15)

        out = np.matmul(self.probs, self.v)
        out = out.transpose(0, 2, 1, 3).reshape(B, T, C)

        self.attn_out = out
        return out.dot(self.W_o)

    def backward(self, dout):
        B, T, C = self.x.shape
        H, D = self.n_head, self.d_head

        self.dW_o = self.attn_out.transpose(0, 2, 1).reshape(C, -1).dot(dout.reshape(-1, C))
        dout_scaled = dout.dot(self.W_o.T).reshape(B, T, H, D).transpose(0, 2, 1, 3)

        dprobs = np.matmul(dout_scaled, self.v.transpose(0, 1, 3, 2))
        dv = np.matmul(self.probs.transpose(0, 1, 3, 2), dout_scaled)

        dscores = self.probs * (dprobs - np.sum(dprobs * self.probs, axis=-1, keepdims=True))
        dscores[:, :, self.mask_indices] = 0.0
        dscores /= np.sqrt(D)

        dq = np.matmul(dscores, self.k)
        dk = np.matmul(dscores.transpose(0, 1, 3, 2), self.q)

        dq = dq.transpose(0, 2, 1, 3).reshape(B * T, C)
        dk = dk.transpose(0, 2, 1, 3).reshape(B * T, C)
        dv = dv.transpose(0, 2, 1, 3).reshape(B * T, C)
        x_flat = self.x.reshape(B * T, C)

        self.dW_q = x_flat.T.dot(dq)
        self.dW_k = x_flat.T.dot(dk)
        self.dW_v = x_flat.T.dot(dv)

        dx = dq.dot(self.W_q.T) + dk.dot(self.W_k.T) + dv.dot(self.W_v.T)
        return dx.reshape(B, T, C)


class MLP:
    def __init__(self, d_model, d_ff):
        limit1 = np.sqrt(6.0 / (d_model + d_ff))
        self.W1 = np.random.uniform(-limit1, limit1, (d_model, d_ff)).astype(np.float32)
        self.b1 = np.zeros(d_ff, dtype=np.float32)

        limit2 = np.sqrt(6.0 / (d_ff + d_model))
        self.W2 = np.random.uniform(-limit2, limit2, (d_ff, d_model)).astype(np.float32)
        self.b2 = np.zeros(d_model, dtype=np.float32)

        self.dW1, self.db1, self.dW2, self.db2 = None, None, None, None

    def forward(self, x):
        self.x = x
        self.h1 = x.dot(self.W1) + self.b1
        self.a1 = gelu(self.h1)
        return self.a1.dot(self.W2) + self.b2

    def backward(self, dout):
        B, T, C = dout.shape
        dout_flat = dout.reshape(-1, C)
        a1_flat = self.a1.reshape(-1, self.W2.shape[0])

        self.dW2 = a1_flat.T.dot(dout_flat)
        self.db2 = np.sum(dout_flat, axis=0)

        da1 = dout_flat.dot(self.W2.T)
        dh1 = da1 * gelu_prime(self.h1.reshape(-1, self.W2.shape[0]))

        x_flat = self.x.reshape(-1, C)
        self.dW1 = x_flat.T.dot(dh1)
        self.db1 = np.sum(dh1, axis=0)

        dx = dh1.dot(self.W1.T)
        return dx.reshape(B, T, C)


class Embedding:
    def __init__(self, num_embeddings, embedding_dim):
        self.weight = np.random.randn(num_embeddings, embedding_dim).astype(np.float32) * 0.02
        self.dweight = None

    def forward(self, idx):
        self.idx = idx
        return self.weight[idx]

    def backward(self, dout):
        self.dweight = np.zeros_like(self.weight)
        np.add.at(self.dweight, self.idx, dout)
        return None
