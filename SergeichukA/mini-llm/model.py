import numpy as np
from layers import Linear, LayerNorm, TransformerBlock

class TransformerLM:
    def __init__(self, vocab_size, d_model, n_layer, n_head, max_seq_len):
        self.d_model = d_model
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        
        self.token_embedding = np.random.randn(vocab_size, d_model) * 0.02
        self.pos_embedding = np.random.randn(max_seq_len, d_model) * 0.02
        self.token_embedding_grad = np.zeros_like(self.token_embedding)
        self.pos_embedding_grad = np.zeros_like(self.pos_embedding)
        
        self.blocks = [TransformerBlock(d_model, n_head) for _ in range(n_layer)]
        self.ln_f = LayerNorm(d_model)
        self.head = Linear(d_model, vocab_size)
        
        self.input_tokens = None

    def get_all_params_with_grads(self):
        params = {
            'token_embedding': (self.token_embedding, self.token_embedding_grad),
            'pos_embedding': (self.pos_embedding, self.pos_embedding_grad),
        }
        
        def add_layer_params(prefix, layer):
            for name in layer._param_names:
                param = getattr(layer, name)
                grad = getattr(layer, f'{name}_grad')
                params[f'{prefix}_{name}'] = (param, grad)
        
        add_layer_params('head', self.head)
        add_layer_params('ln_f', self.ln_f)
        
        for i, block in enumerate(self.blocks):
            add_layer_params(f'block{i}_ln1', block.ln1)
            add_layer_params(f'block{i}_attn_q', block.attn.q_proj)
            add_layer_params(f'block{i}_attn_k', block.attn.k_proj)
            add_layer_params(f'block{i}_attn_v', block.attn.v_proj)
            add_layer_params(f'block{i}_attn_o', block.attn.out_proj)
            add_layer_params(f'block{i}_ln2', block.ln2)
            add_layer_params(f'block{i}_mlp_fc1', block.mlp.fc1)
            add_layer_params(f'block{i}_mlp_fc2', block.mlp.fc2)
        
        return params

    def zero_grad(self):
        self.token_embedding_grad[:] = 0
        self.pos_embedding_grad[:] = 0
        self.head.zero_grad()
        self.ln_f.zero_grad()
        for block in self.blocks:
            block.zero_grad()

    def forward(self, x):
        self.input_tokens = x
        B, T = x.shape
        
        tok_emb = self.token_embedding[x]
        pos_emb = self.pos_embedding[:T, :]
        x = tok_emb + pos_emb
        
        for block in self.blocks:
            x = block.forward(x)
            
        x = self.ln_f.forward(x)
        logits = self.head.forward(x)
        return logits

    def backward(self, dout):
        dx = self.head.backward(dout)
        dx = self.ln_f.backward(dx)
        
        for block in reversed(self.blocks):
            dx = block.backward(dx)
            
        self.pos_embedding_grad[:] = dx.sum(axis=0)
        
        B, T, D = dx.shape
        self.token_embedding_grad[:] = 0
        indices = self.input_tokens.reshape(-1)
        grads = dx.reshape(-1, D)
        np.add.at(self.token_embedding_grad, indices, grads)
