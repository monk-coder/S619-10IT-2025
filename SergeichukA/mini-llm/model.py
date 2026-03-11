import numpy as np
from layers import Linear, LayerNorm, TransformerBlock

class TransformerLM:
    def __init__(self, vocab_size, d_model, n_layer, n_head, max_seq_len):
        self.token_embedding = np.random.randn(vocab_size, d_model) * 0.02
        self.pos_embedding = np.random.randn(max_seq_len, d_model) * 0.02
        
        self.blocks = [TransformerBlock(d_model, n_head) for _ in range(n_layer)]
        self.ln_f = LayerNorm(d_model)
        self.head = Linear(d_model, vocab_size)
        
        self.d_model = d_model
        self.cache = None

    def parameters(self):
        params = {'token_embedding': self.token_embedding, 'pos_embedding': self.pos_embedding}
        params.update(self.head.parameters())
        params.update(self.ln_f.parameters())
        for i, block in enumerate(self.blocks):
            params.update({f'block_{i}_{k}': v for k, v in block.parameters().items()})
        return params

    def zero_grad(self):
        for p in self.parameters().values():
            if isinstance(p, np.ndarray):
                # We need to track gradients manually in a dict for the optimizer
                pass 
        # Gradients are stored inside layer objects (e.g., self.head.w_grad)
        self.head.zero_grad()
        self.ln_f.zero_grad()
        for block in self.blocks:
            block.ln1.zero_grad()
            block.attn.q_proj.zero_grad()
            block.attn.k_proj.zero_grad()
            block.attn.v_proj.zero_grad()
            block.attn.out_proj.zero_grad()
            block.ln2.zero_grad()
            block.mlp.fc1.zero_grad()
            block.mlp.fc2.zero_grad()

    def forward(self, x):
        # x: (B, T)
        B, T = x.shape
        tok_emb = self.token_embedding[x] # (B, T, d_model)
        pos_emb = self.pos_embedding[:T, :] # (T, d_model)
        x = tok_emb + pos_emb
        
        for block in self.blocks:
            x = block.forward(x)
            
        x = self.ln_f.forward(x)
        logits = self.head.forward(x)
        return logits

    def backward(self, dout):
        # dout: (B, T, vocab_size)
        dx = self.head.backward(dout)
        dx = self.ln_f.backward(dx)
        
        for block in reversed(self.blocks):
            dx = block.backward(dx)
            
        # Gradients for embeddings
        # dx is (B, T, d_model). 
        # token_embedding grad: scatter_add dx to indices x
        # pos_embedding grad: sum dx over batch
        self.token_embedding_grad = np.zeros_like(self.token_embedding)
        np.add.at(self.token_embedding_grad, x_indices_flat, dx_flat) # Need to implement carefully
        
        # Simplified embedding grad for this snippet:
        # We need x (input tokens) in backward. 
        # Let's assume we stored x in forward.
        pass 