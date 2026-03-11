import numpy as np
from layers import Embedding, Linear, LayerNorm, TransformerBlock, Module

class TransformerLM(Module):
    def __init__(self, vocab_size, d_model, n_head, n_layer, max_seq_len, d_ff=None):
        super().__init__()
        if d_ff is None:
            d_ff = 4 * d_model
            
        self.token_emb = Embedding(vocab_size, d_model)
        self.pos_emb = Embedding(max_seq_len, d_model)
        
        self.blocks = []
        for _ in range(n_layer):
            block = TransformerBlock(d_model, n_head, d_ff)
            self.blocks.append(block)
            # Link params/grads from blocks
            self.params.update(block.params)
            self.grads.update(block.grads)
            
        self.ln_f = LayerNorm(d_model)
        self.head = Linear(d_model, vocab_size)
        
        # Link remaining params
        self.params.update(self.token_emb.params)
        self.params.update(self.pos_emb.params)
        self.params.update(self.ln_f.params)
        self.params.update(self.head.params)
        
        self.grads.update(self.token_emb.grads)
        self.grads.update(self.pos_emb.grads)
        self.grads.update(self.ln_f.grads)
        self.grads.update(self.head.grads)

    def forward(self, idx):
        B, T = idx.shape
        pos = np.arange(0, T).reshape(1, T)
        
        x = self.token_emb.forward(idx) + self.pos_emb.forward(pos)
        
        for block in self.blocks:
            x = block.forward(x)
            
        x = self.ln_f.forward(x)
        logits = self.head.forward(x)
        return logits

    def backward(self, dlogits):
        dx = self.head.backward(dlogits)
        dx = self.ln_f.backward(dx)
        
        for block in reversed(self.blocks):
            dx = block.backward(dx)
            
        self.pos_emb.backward(dx) 
        self.token_emb.backward(dx)

    def zero_grad(self):
        """Рекурсивно обнуляет все градиенты"""
        for k in self.grads:
            if self.grads[k] is not None:
                self.grads[k][:] = 0