# models/transformer_lm.py
import numpy as np
from typing import List, Optional
from .transformer_block import TransformerBlock  # Используем относительный импорт с точкой
from layers.layer_norm import LayerNorm
from layers.embeddings import TokenEmbedding, PositionalEmbedding
from utils.helpers import softmax, create_causal_mask


class TransformerLM:
    def __init__(self, vocab_size, d_model, n_head, n_layer, max_seq_len, d_ff=None):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_head = n_head
        self.n_layer = n_layer
        self.max_seq_len = max_seq_len

        if d_ff is None:
            d_ff = 4 * d_model
        self.d_ff = d_ff

        # Эмбеддинги
        self.token_embedding = TokenEmbedding(vocab_size, d_model)
        self.pos_embedding = PositionalEmbedding(max_seq_len, d_model)

        # Стек трансформеров
        self.blocks = [TransformerBlock(d_model, n_head, d_ff) for _ in range(n_layer)]

        # Выходной слой
        self.ln_final = LayerNorm(d_model)
        scale = 1 / np.sqrt(d_model)
        self.output_proj = np.random.randn(d_model, vocab_size) * scale
        self.d_output_proj = np.zeros_like(self.output_proj)

        # Для backward
        self.cache = {}

        # Causal mask
        self.causal_mask = create_causal_mask(max_seq_len)

    def forward(self, x, return_logits=True):
        """
        x: (batch_size, seq_len) - индексы токенов
        """
        B, T = x.shape
        assert T <= self.max_seq_len, f"Sequence length {T} exceeds max_seq_len {self.max_seq_len}"

        # Сохраняем для backward
        self.cache['x'] = x
        self.cache['T'] = T
        self.cache['B'] = B

        # Получаем эмбеддинги токенов
        token_emb = self.token_embedding.forward(x)  # (B, T, d_model)

        # Добавляем позиционные эмбеддинги
        pos_emb = self.pos_embedding.forward(T)  # (1, T, d_model)
        x = token_emb + pos_emb

        self.cache['token_emb'] = token_emb
        self.cache['pos_emb'] = pos_emb
        self.cache['embedding_out'] = x

        # Проход через блоки трансформера
        for i, block in enumerate(self.blocks):
            x = block.forward(x, self.causal_mask[:T, :T])
            self.cache[f'block_{i}_out'] = x

        # Финальная нормализация
        x = self.ln_final.forward(x)
        self.cache['final_norm'] = x

        # Проекция на словарь
        logits = x @ self.output_proj

        if return_logits:
            return logits
        else:
            # Возвращаем вероятности для генерации
            return softmax(logits, axis=-1)

    def backward(self, dlogits):
        """
        dlogits: (batch_size, seq_len, vocab_size) - градиент потерь по logits
        """
        B, T, V = dlogits.shape

        # Градиент для выходной проекции
        final_norm = self.cache['final_norm']
        self.d_output_proj = final_norm.reshape(-1, self.d_model).T @ dlogits.reshape(-1, V)

        # Градиент для финальной нормализации
        dx = dlogits @ self.output_proj.T
        dx = self.ln_final.backward(dx)

        # Обратный проход через блоки (в обратном порядке)
        for i in reversed(range(self.n_layer)):
            dx = self.blocks[i].backward(dx)

        # Градиенты для эмбеддингов
        # Сначала для позиционных эмбеддингов
        self.pos_embedding.backward(dx)

        # Затем для эмбеддингов токенов
        self.token_embedding.backward(dx)

        return dx

    def get_parameters(self):
        """Возвращает все параметры модели и их градиенты"""
        params = [
            (self.output_proj, self.d_output_proj)
        ]
        params.extend(self.token_embedding.get_parameters())
        params.extend(self.pos_embedding.get_parameters())
        params.extend(self.ln_final.get_parameters())
        for block in self.blocks:
            params.extend(block.get_parameters())
        return params

    def zero_grad(self):
        """Обнуляет все градиенты"""
        self.d_output_proj.fill(0)
        self.token_embedding.zero_grad()
        self.pos_embedding.zero_grad()
        self.ln_final.zero_grad()
        for block in self.blocks:
            block.zero_grad()
        self.cache = {}

    def generate(self, prompt, max_new_tokens, temperature=1.0, top_k=None):
        """
        Генерирует текст из промпта

        prompt: список индексов токенов (1D массив)
        max_new_tokens: максимальное количество новых токенов
        temperature: температура для сэмплирования
        top_k: если указан, оставляет только top_k токенов
        """
        generated = list(prompt)

        for _ in range(max_new_tokens):
            # Берем последние max_seq_len токенов
            context = generated[-self.max_seq_len:]

            # Преобразуем в батч размера 1
            x = np.array([context])

            # Forward pass (получаем вероятности)
            probs = self.forward(x, return_logits=False)

            # Берем вероятности для последнего токена
            next_token_probs = probs[0, -1, :].copy()

            # Температура
            if temperature != 1.0:
                next_token_probs = next_token_probs ** (1.0 / temperature)
                next_token_probs = next_token_probs / np.sum(next_token_probs)

            # Top-k фильтрация
            if top_k is not None:
                indices = np.argsort(next_token_probs)[-top_k:]
                mask = np.ones_like(next_token_probs) * 1e-8
                mask[indices] = 1
                next_token_probs = next_token_probs * mask
                next_token_probs = next_token_probs / np.sum(next_token_probs)

            # Сэмплируем следующий токен
            next_token = np.random.choice(len(next_token_probs), p=next_token_probs)

            generated.append(next_token)

        return np.array(generated)