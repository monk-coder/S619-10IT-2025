import numpy as np
from layers.layer_norm import LayerNorm
from layers.attention import MultiHeadAttention
from layers.mlp import MLP


class TransformerBlock:
    def __init__(self, d_model, n_head, d_ff):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, n_head)
        self.ln2 = LayerNorm(d_model)
        self.mlp = MLP(d_model, d_ff)

    def forward(self, x, mask=None):
        # Первый residual block: Attention + LayerNorm
        attn_out = self.attn.forward(self.ln1.forward(x), mask)
        x = x + attn_out

        # Второй residual block: MLP + LayerNorm
        mlp_out = self.mlp.forward(self.ln2.forward(x))
        x = x + mlp_out

        return x

    def backward(self, dout):
        # Обратный проход через второй residual block
        dmlp = dout
        dln2 = self.mlp.backward(dmlp)
        dresidual2 = self.ln2.backward(dln2)
        dout = dout + dresidual2  # residual connection

        # Обратный проход через первый residual block
        dattn = dout
        dln1 = self.attn.backward(dattn)
        dresidual1 = self.ln1.backward(dln1)
        dout = dout + dresidual1  # residual connection

        return dout

    def get_parameters(self):
        params = []
        params.extend(self.ln1.get_parameters())
        params.extend(self.attn.get_parameters())
        params.extend(self.ln2.get_parameters())
        params.extend(self.mlp.get_parameters())
        return params

    def zero_grad(self):
        self.ln1.zero_grad()
        self.attn.zero_grad()
        self.ln2.zero_grad()
        self.mlp.zero_grad()